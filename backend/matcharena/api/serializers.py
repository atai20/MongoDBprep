from __future__ import annotations

from matcharena.domain.elo import RatingWindow
from matcharena.domain.models import Game, Match, Player, QueueEntry
from matcharena.services.matchmaking_service import CurrentMatchView, QueueStatusView
from matcharena.services.player_service import PlayerProfile


def player_public(player: Player) -> dict:
    return {
        "player_id": player.player_id,
        "username": player.username,
        "rating": player.rating,
        "status": player.status.value,
        "created_at": player.created_at.isoformat(),
        "updated_at": player.updated_at.isoformat(),
    }


def player_private(player: Player, token: str | None = None) -> dict:
    payload = player_public(player)
    if token is not None:
        payload["token"] = token
    return payload


def queue_entry(entry: QueueEntry) -> dict:
    return {
        "queue_id": entry.queue_id,
        "player_id": entry.player_id,
        "rating": entry.rating,
        "status": entry.status.value,
        "created_at": entry.created_at.isoformat(),
        "updated_at": entry.updated_at.isoformat(),
        "match_id": entry.match_id,
    }


def match_public(match: Match) -> dict:
    return {
        "match_id": match.match_id,
        "player_ids": match.player_ids,
        "status": match.status.value,
        "created_at": match.created_at.isoformat(),
        "game_id": match.game_id,
        "rating_spread": match.rating_spread,
    }


def game_public(game: Game) -> dict:
    return {
        "game_id": game.game_id,
        "match_id": game.match_id,
        "player_ids": game.player_ids,
        "capacity": game.capacity,
        "status": game.status.value,
        "created_at": game.created_at.isoformat(),
        "host_id": game.host_id,
        "name": game.name,
        "slots_remaining": max(0, game.capacity - len(game.player_ids)),
    }


def rating_window(window: RatingWindow | None) -> dict | None:
    if window is None:
        return None
    return {"lower": window.lower, "upper": window.upper}


def queue_status(view: QueueStatusView) -> dict:
    return {
        "state": view.state,
        "wait_seconds": view.wait_seconds,
        "tolerance": view.tolerance,
        "window": rating_window(view.window),
        "entry": queue_entry(view.entry) if view.entry else None,
        "match": match_public(view.match) if view.match else None,
    }


def current_match(view: CurrentMatchView) -> dict:
    return {
        "match": match_public(view.match),
        "game": game_public(view.game) if view.game else None,
        "players": [player_public(p) for p in view.players],
    }


def profile(view: PlayerProfile) -> dict:
    return {
        "player": player_public(view.player),
        "recent_queue_entries": [queue_entry(e) for e in view.recent_queue_entries],
        "recent_matches": [match_public(m) for m in view.recent_matches],
    }
