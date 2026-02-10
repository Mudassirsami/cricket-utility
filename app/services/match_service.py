from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.match import (
    Match, Innings, BallEvent, MatchStatus, InningsStatus, ExtraType, DismissalType
)
from app.schemas.match import (
    CreateMatchRequest, SetTossRequest, StartInningsRequest,
    RecordBallRequest, ChangeBowlerRequest,
    MatchResponse, MatchListItem, BallEventResponse,
    FullScorecard, InningsScorecard, BatsmanStats, BowlerStats,
)


class MatchService:

    @staticmethod
    async def _get_innings_by_id(db: AsyncSession, innings_id: str) -> Innings:
        stmt = (
            select(Innings)
            .options(selectinload(Innings.balls))
            .where(Innings.id == innings_id)
        )
        result = await db.execute(stmt)
        innings = result.scalar_one_or_none()
        if not innings:
            raise HTTPException(status_code=404, detail="Innings not found.")
        return innings

    @staticmethod
    async def create_match(db: AsyncSession, req: CreateMatchRequest) -> Match:
        match = Match(
            team_a_name=req.team_a_name.strip(),
            team_b_name=req.team_b_name.strip(),
            total_overs=req.total_overs,
            venue=req.venue.strip() if req.venue else None,
            status=MatchStatus.TOSS,
        )
        db.add(match)
        await db.commit()
        await db.refresh(match)
        return match

    @staticmethod
    async def get_match(db: AsyncSession, match_id: str) -> Match:
        stmt = (
            select(Match)
            .options(
                selectinload(Match.innings).selectinload(Innings.balls)
            )
            .where(Match.id == match_id)
        )
        result = await db.execute(stmt)
        match = result.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found.")
        return match

    @staticmethod
    async def list_matches(db: AsyncSession) -> List[Match]:
        stmt = select(Match).order_by(Match.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def set_toss(db: AsyncSession, match_id: str, req: SetTossRequest) -> Match:
        match = await MatchService.get_match(db, match_id)
        if match.status != MatchStatus.TOSS:
            raise HTTPException(status_code=400, detail="Toss can only be set when match is in TOSS state.")
        if req.toss_winner not in (match.team_a_name, match.team_b_name):
            raise HTTPException(status_code=400, detail="Toss winner must be one of the two teams.")
        match.toss_winner = req.toss_winner
        match.toss_decision = req.toss_decision
        match.status = MatchStatus.IN_PROGRESS
        await db.commit()
        await db.refresh(match)
        return match

    @staticmethod
    async def start_innings(db: AsyncSession, match_id: str, req: StartInningsRequest) -> Innings:
        match = await MatchService.get_match(db, match_id)
        if match.status not in (MatchStatus.IN_PROGRESS, MatchStatus.INNINGS_BREAK):
            raise HTTPException(status_code=400, detail="Cannot start innings in current match state.")

        existing_innings_count = len(match.innings)
        if existing_innings_count >= 2:
            raise HTTPException(status_code=400, detail="Both innings already exist.")

        innings_number = existing_innings_count + 1

        if req.batting_team not in (match.team_a_name, match.team_b_name):
            raise HTTPException(status_code=400, detail="Batting team must be one of the match teams.")
        if req.bowling_team not in (match.team_a_name, match.team_b_name):
            raise HTTPException(status_code=400, detail="Bowling team must be one of the match teams.")
        if req.batting_team == req.bowling_team:
            raise HTTPException(status_code=400, detail="Batting and bowling teams cannot be the same.")

        target = None
        if innings_number == 2 and len(match.innings) == 1:
            first_innings = match.innings[0]
            target = first_innings.total_runs + 1

        innings = Innings(
            match_id=match_id,
            innings_number=innings_number,
            batting_team=req.batting_team.strip(),
            bowling_team=req.bowling_team.strip(),
            status=InningsStatus.IN_PROGRESS,
            target=target,
            striker_name=req.striker_name.strip(),
            non_striker_name=req.non_striker_name.strip(),
            current_bowler_name=req.bowler_name.strip(),
        )
        db.add(innings)
        match.status = MatchStatus.IN_PROGRESS
        await db.commit()
        return await MatchService._get_innings_by_id(db, innings.id)

    @staticmethod
    async def _get_active_innings(db: AsyncSession, match_id: str) -> tuple:
        match = await MatchService.get_match(db, match_id)
        active_innings = None
        for inn in match.innings:
            if inn.status == InningsStatus.IN_PROGRESS:
                active_innings = inn
                break
        if not active_innings:
            raise HTTPException(status_code=400, detail="No active innings found.")
        return match, active_innings

    @staticmethod
    async def record_ball(db: AsyncSession, match_id: str, req: RecordBallRequest) -> dict:
        match, innings = await MatchService._get_active_innings(db, match_id)

        if req.is_wicket and not req.dismissal_type:
            raise HTTPException(status_code=400, detail="Dismissal type is required for a wicket.")
        if req.is_wicket and not req.dismissed_batsman:
            raise HTTPException(status_code=400, detail="Dismissed batsman name is required for a wicket.")
        if req.is_boundary_four and req.is_boundary_six:
            raise HTTPException(status_code=400, detail="Ball cannot be both four and six.")

        is_legal = req.extra_type not in (ExtraType.WIDE, ExtraType.NO_BALL)

        active_balls = [b for b in innings.balls if not b.is_undone]
        sequence_number = len(active_balls) + 1

        ball_event = BallEvent(
            innings_id=innings.id,
            sequence_number=sequence_number,
            over_number=innings.current_over,
            ball_number=innings.current_ball if is_legal else innings.current_ball,
            bowler_name=innings.current_bowler_name,
            batsman_name=innings.striker_name,
            non_striker_name=innings.non_striker_name,
            runs_scored=req.runs_scored,
            is_boundary_four=req.is_boundary_four,
            is_boundary_six=req.is_boundary_six,
            extra_type=req.extra_type,
            extra_runs=req.extra_runs,
            is_wicket=req.is_wicket,
            dismissal_type=req.dismissal_type,
            dismissed_batsman=req.dismissed_batsman,
            fielder_name=req.fielder_name,
            is_legal_delivery=is_legal,
        )
        db.add(ball_event)

        total_runs_this_ball = req.runs_scored + req.extra_runs
        innings.total_runs += total_runs_this_ball

        if req.extra_type == ExtraType.WIDE:
            innings.extras_wides += req.extra_runs
        elif req.extra_type == ExtraType.NO_BALL:
            innings.extras_no_balls += req.extra_runs
        elif req.extra_type == ExtraType.BYE:
            innings.extras_byes += req.extra_runs
        elif req.extra_type == ExtraType.LEG_BYE:
            innings.extras_leg_byes += req.extra_runs

        if req.is_wicket:
            innings.total_wickets += 1

        should_rotate_strike = False
        if is_legal:
            innings.current_ball += 1
            if req.runs_scored % 2 == 1:
                should_rotate_strike = True
        else:
            if req.extra_type == ExtraType.NO_BALL and req.runs_scored % 2 == 1:
                should_rotate_strike = True

        over_complete = False
        if is_legal and innings.current_ball >= 6:
            innings.current_ball = 0
            innings.current_over += 1
            innings.total_overs_bowled = float(innings.current_over)
            over_complete = True
            should_rotate_strike = not should_rotate_strike
        elif is_legal:
            innings.total_overs_bowled = float(innings.current_over) + (innings.current_ball / 10.0)

        if should_rotate_strike:
            innings.striker_name, innings.non_striker_name = innings.non_striker_name, innings.striker_name

        if req.is_wicket and req.new_batsman_name:
            if req.dismissed_batsman == ball_event.batsman_name:
                if should_rotate_strike:
                    innings.non_striker_name = req.new_batsman_name.strip()
                else:
                    innings.striker_name = req.new_batsman_name.strip()
            else:
                if should_rotate_strike:
                    innings.striker_name = req.new_batsman_name.strip()
                else:
                    innings.non_striker_name = req.new_batsman_name.strip()

        innings_ended = False
        result_summary = None

        if innings.total_wickets >= 10:
            innings.status = InningsStatus.COMPLETED
            innings_ended = True
        elif innings.current_over >= match.total_overs and innings.current_ball == 0:
            innings.status = InningsStatus.COMPLETED
            innings_ended = True
        elif innings.innings_number == 2 and innings.target and innings.total_runs >= innings.target:
            innings.status = InningsStatus.COMPLETED
            innings_ended = True

        if innings_ended:
            if innings.innings_number == 1:
                match.status = MatchStatus.INNINGS_BREAK
            else:
                match.status = MatchStatus.COMPLETED
                result_summary = MatchService._calculate_result(match, innings)
                match.result_summary = result_summary

        await db.commit()
        await db.refresh(innings)

        return {
            "ball_event": ball_event,
            "innings": innings,
            "over_complete": over_complete,
            "innings_ended": innings_ended,
            "result_summary": result_summary,
        }

    @staticmethod
    def _calculate_result(match: Match, second_innings: Innings) -> str:
        first_innings = match.innings[0]
        if second_innings.total_runs >= second_innings.target:
            wickets_remaining = 10 - second_innings.total_wickets
            return f"{second_innings.batting_team} won by {wickets_remaining} wicket(s)"
        else:
            run_diff = first_innings.total_runs - second_innings.total_runs
            return f"{first_innings.batting_team} won by {run_diff} run(s)"

    @staticmethod
    async def undo_last_ball(db: AsyncSession, match_id: str) -> dict:
        match, innings = await MatchService._get_active_innings(db, match_id)
        active_balls = [b for b in innings.balls if not b.is_undone]
        if not active_balls:
            raise HTTPException(status_code=400, detail="No balls to undo.")

        last_ball = active_balls[-1]
        last_ball.is_undone = True

        total_runs_this_ball = last_ball.runs_scored + last_ball.extra_runs
        innings.total_runs -= total_runs_this_ball

        if last_ball.extra_type == ExtraType.WIDE:
            innings.extras_wides -= last_ball.extra_runs
        elif last_ball.extra_type == ExtraType.NO_BALL:
            innings.extras_no_balls -= last_ball.extra_runs
        elif last_ball.extra_type == ExtraType.BYE:
            innings.extras_byes -= last_ball.extra_runs
        elif last_ball.extra_type == ExtraType.LEG_BYE:
            innings.extras_leg_byes -= last_ball.extra_runs

        if last_ball.is_wicket:
            innings.total_wickets -= 1

        if last_ball.is_legal_delivery:
            if innings.current_ball == 0 and innings.current_over > 0:
                innings.current_over -= 1
                innings.current_ball = 5
            else:
                innings.current_ball -= 1
            innings.total_overs_bowled = float(innings.current_over) + (innings.current_ball / 10.0)

        innings.striker_name = last_ball.batsman_name
        innings.non_striker_name = last_ball.non_striker_name
        innings.current_bowler_name = last_ball.bowler_name

        await db.commit()
        refreshed = await MatchService._get_innings_by_id(db, innings.id)
        return {"message": "Last ball undone.", "innings": refreshed}

    @staticmethod
    async def change_bowler(db: AsyncSession, match_id: str, req: ChangeBowlerRequest) -> Innings:
        _, innings = await MatchService._get_active_innings(db, match_id)
        if innings.current_ball != 0:
            raise HTTPException(status_code=400, detail="Bowler can only be changed at the start of an over.")
        innings.current_bowler_name = req.bowler_name.strip()
        await db.commit()
        return await MatchService._get_innings_by_id(db, innings.id)

    @staticmethod
    async def swap_strike(db: AsyncSession, match_id: str) -> Innings:
        _, innings = await MatchService._get_active_innings(db, match_id)
        innings.striker_name, innings.non_striker_name = innings.non_striker_name, innings.striker_name
        await db.commit()
        return await MatchService._get_innings_by_id(db, innings.id)

    @staticmethod
    async def end_innings(db: AsyncSession, match_id: str) -> Match:
        match, innings = await MatchService._get_active_innings(db, match_id)
        innings.status = InningsStatus.COMPLETED
        if innings.innings_number == 1:
            match.status = MatchStatus.INNINGS_BREAK
        else:
            match.status = MatchStatus.COMPLETED
            match.result_summary = MatchService._calculate_result(match, innings)
        await db.commit()
        return await MatchService.get_match(db, match_id)

    @staticmethod
    async def abandon_match(db: AsyncSession, match_id: str) -> Match:
        match = await MatchService.get_match(db, match_id)
        if match.status == MatchStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Cannot abandon a completed match.")
        match.status = MatchStatus.ABANDONED
        match.result_summary = "Match Abandoned"
        for inn in match.innings:
            if inn.status == InningsStatus.IN_PROGRESS:
                inn.status = InningsStatus.COMPLETED
        await db.commit()
        return await MatchService.get_match(db, match_id)

    @staticmethod
    async def delete_match(db: AsyncSession, match_id: str) -> None:
        match = await MatchService.get_match(db, match_id)
        if match.status not in (MatchStatus.COMPLETED, MatchStatus.ABANDONED):
            raise HTTPException(status_code=400, detail="Only completed or abandoned matches can be deleted.")
        await db.delete(match)
        await db.commit()

    @staticmethod
    async def get_scorecard(db: AsyncSession, match_id: str) -> FullScorecard:
        match = await MatchService.get_match(db, match_id)
        match_info = MatchListItem.model_validate(match)

        innings_cards = []
        for inn in match.innings:
            active_balls = [b for b in inn.balls if not b.is_undone]
            batsmen_map = {}
            bowler_map = {}
            fow = []

            for ball in active_balls:
                bname = ball.batsman_name
                if bname not in batsmen_map:
                    batsmen_map[bname] = {
                        "runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0,
                        "how_out": "not out", "bowler": None
                    }
                if ball.is_legal_delivery or ball.extra_type == ExtraType.NO_BALL:
                    batsmen_map[bname]["balls_faced"] += 1
                if ball.extra_type not in (ExtraType.WIDE, ExtraType.BYE, ExtraType.LEG_BYE):
                    batsmen_map[bname]["runs"] += ball.runs_scored
                if ball.is_boundary_four:
                    batsmen_map[bname]["fours"] += 1
                if ball.is_boundary_six:
                    batsmen_map[bname]["sixes"] += 1

                if ball.is_wicket and ball.dismissed_batsman:
                    d = ball.dismissed_batsman
                    if d not in batsmen_map:
                        batsmen_map[d] = {
                            "runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0,
                            "how_out": "not out", "bowler": None
                        }
                    dismissal_str = ball.dismissal_type.value if ball.dismissal_type else "out"
                    if ball.fielder_name:
                        dismissal_str = f"c {ball.fielder_name} b {ball.bowler_name}"
                        if ball.dismissal_type == DismissalType.BOWLED:
                            dismissal_str = f"b {ball.bowler_name}"
                        elif ball.dismissal_type == DismissalType.LBW:
                            dismissal_str = f"lbw b {ball.bowler_name}"
                        elif ball.dismissal_type == DismissalType.RUN_OUT:
                            dismissal_str = f"run out ({ball.fielder_name})"
                        elif ball.dismissal_type == DismissalType.STUMPED:
                            dismissal_str = f"st {ball.fielder_name} b {ball.bowler_name}"
                    else:
                        if ball.dismissal_type == DismissalType.BOWLED:
                            dismissal_str = f"b {ball.bowler_name}"
                        elif ball.dismissal_type == DismissalType.LBW:
                            dismissal_str = f"lbw b {ball.bowler_name}"
                        elif ball.dismissal_type == DismissalType.CAUGHT:
                            dismissal_str = f"c & b {ball.bowler_name}"
                        elif ball.dismissal_type == DismissalType.HIT_WICKET:
                            dismissal_str = f"hit wicket b {ball.bowler_name}"
                        elif ball.dismissal_type == DismissalType.RUN_OUT:
                            dismissal_str = "run out"
                    batsmen_map[d]["how_out"] = dismissal_str
                    batsmen_map[d]["bowler"] = ball.bowler_name
                    running_total = inn.total_runs  # simplified
                    fow.append({
                        "wicket_number": len(fow) + 1,
                        "batsman": d,
                        "score": f"{ball.over_number}.{ball.ball_number}",
                    })

                bowler = ball.bowler_name
                if bowler not in bowler_map:
                    bowler_map[bowler] = {
                        "balls": 0, "maidens": 0, "runs_conceded": 0,
                        "wickets": 0, "wides": 0, "no_balls": 0,
                        "current_over_runs": 0, "current_over_balls": 0,
                        "current_over_num": ball.over_number,
                    }
                bm = bowler_map[bowler]
                if ball.is_legal_delivery:
                    bm["balls"] += 1
                    bm["current_over_balls"] += 1
                if ball.extra_type == ExtraType.WIDE:
                    bm["wides"] += 1
                    bm["runs_conceded"] += ball.extra_runs
                elif ball.extra_type == ExtraType.NO_BALL:
                    bm["no_balls"] += 1
                    bm["runs_conceded"] += ball.extra_runs + ball.runs_scored
                elif ball.extra_type in (ExtraType.BYE, ExtraType.LEG_BYE):
                    pass
                else:
                    bm["runs_conceded"] += ball.runs_scored

                if ball.is_wicket and ball.dismissal_type not in (DismissalType.RUN_OUT, DismissalType.RETIRED_HURT, DismissalType.OBSTRUCTING):
                    bm["wickets"] += 1

                bm["current_over_runs"] += ball.runs_scored + ball.extra_runs
                if ball.over_number != bm["current_over_num"]:
                    if bm["current_over_runs"] == 0 and bm["current_over_balls"] == 6:
                        bm["maidens"] += 1
                    bm["current_over_runs"] = 0
                    bm["current_over_balls"] = 0
                    bm["current_over_num"] = ball.over_number

            non_striker = inn.non_striker_name
            if non_striker and non_striker not in batsmen_map:
                batsmen_map[non_striker] = {
                    "runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0,
                    "how_out": "not out", "bowler": None
                }

            batsmen_stats = []
            for name, data in batsmen_map.items():
                sr = (data["runs"] / data["balls_faced"] * 100) if data["balls_faced"] > 0 else 0.0
                batsmen_stats.append(BatsmanStats(
                    name=name, runs=data["runs"], balls_faced=data["balls_faced"],
                    fours=data["fours"], sixes=data["sixes"],
                    strike_rate=round(sr, 2),
                    how_out=data["how_out"], bowler=data["bowler"]
                ))

            bowler_stats = []
            for name, data in bowler_map.items():
                overs_int = data["balls"] // 6
                overs_rem = data["balls"] % 6
                overs_str = f"{overs_int}.{overs_rem}" if overs_rem else str(overs_int)
                econ = (data["runs_conceded"] / (data["balls"] / 6)) if data["balls"] > 0 else 0.0
                bowler_stats.append(BowlerStats(
                    name=name,
                    overs=overs_str,
                    maidens=data["maidens"],
                    runs_conceded=data["runs_conceded"],
                    wickets=data["wickets"],
                    economy=round(econ, 2),
                    wides=data["wides"],
                    no_balls=data["no_balls"],
                ))

            overs_int = int(inn.total_overs_bowled)
            overs_rem = inn.current_ball
            total_overs_str = f"{overs_int}.{overs_rem}" if overs_rem else str(overs_int)

            innings_cards.append(InningsScorecard(
                innings_number=inn.innings_number,
                batting_team=inn.batting_team,
                bowling_team=inn.bowling_team,
                total_runs=inn.total_runs,
                total_wickets=inn.total_wickets,
                total_overs=total_overs_str,
                extras={
                    "wides": inn.extras_wides,
                    "no_balls": inn.extras_no_balls,
                    "byes": inn.extras_byes,
                    "leg_byes": inn.extras_leg_byes,
                    "penalties": inn.extras_penalties,
                    "total": inn.extras_wides + inn.extras_no_balls + inn.extras_byes + inn.extras_leg_byes + inn.extras_penalties,
                },
                batsmen=batsmen_stats,
                bowlers=bowler_stats,
                fall_of_wickets=fow,
            ))

        return FullScorecard(match=match_info, innings=innings_cards)
