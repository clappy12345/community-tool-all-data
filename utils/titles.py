TITLES = {
    "NHL": {
        "name": "NHL",
        "full_name": "NHL 26",
        "publisher": "EA Sports",
        "icon": "",
        "genre": "hockey",
        "community_noun": "players",
        "compare_hint": "e.g., NHL 25 launch",
        "ai_context": "the video game NHL 26 by EA Sports (ice hockey)",
        "chatbot_role": "an NHL 26 community data analyst",
        "topic_buckets": {
            "Pokechecks / Stick Play": [
                "pokecheck", "poke check", "poke checking", "stick lift",
                "stick play", "stick check", "tripping", "slash",
            ],
            "Skating / Movement": [
                "skating", "skate", "speed", "momentum", "agility",
                "acceleration", "stride", "edge work", "pivot",
            ],
            "Goalies": [
                "goalie", "goaltender", "goaltending", "saves", "glove",
                "blocker", "butterfly", "goalie movement", "five hole",
            ],
            "Hitting / Physicality": [
                "hitting", "hit", "body check", "bodycheck", "hip check",
                "big hit", "boarding", "fighting", "fight",
            ],
            "HUT / Ultimate Team": [
                "hut", "ultimate team", "pack", "pack pull", "auction",
                "rivals", "rush", "champs", "champions", "squad battles",
                "lineup", "coins", "msp",
            ],
            "EASHL / Online Modes": [
                "eashl", "club", "world of chel", "chel", "online versus",
                "matchmaking", "ranked", "drop-in", "drop in",
            ],
            "Be A Pro / Franchise": [
                "be a pro", "bap", "franchise", "franchise mode", "draft",
                "trade", "scouting", "sim", "simulation",
            ],
            "Servers / Performance": [
                "server", "servers", "lag", "latency", "disconnect",
                "desync", "fps", "crash", "frame rate", "input delay",
            ],
            "Graphics / Presentation": [
                "graphics", "visuals", "presentation", "animation",
                "ice", "arena", "jersey", "crowd", "commentary",
                "replay", "cutscene",
            ],
            "AI / CPU Behavior": [
                "ai", "cpu", "teammate ai", "computer", "difficulty",
                "superstar", "all-star", "sliders",
            ],
        },
    },
    "UFC": {
        "name": "UFC",
        "full_name": "UFC 6",
        "publisher": "EA Sports",
        "icon": "",
        "genre": "mixed martial arts",
        "community_noun": "fans",
        "compare_hint": "e.g., UFC 5 launch",
        "ai_context": "the video game UFC 6 by EA Sports (MMA / mixed martial arts)",
        "chatbot_role": "a UFC 6 community data analyst",
        "topic_buckets": {
            "Striking / Stand-Up": [
                "striking", "stand up", "standup", "boxing", "punch",
                "kick", "combo", "ko", "knockout", "head movement",
            ],
            "Grappling / Ground Game": [
                "grappling", "ground game", "takedown", "wrestling",
                "submission", "ground and pound", "gnp", "clinch",
                "sprawl", "guard",
            ],
            "Career Mode": [
                "career", "career mode", "story", "storyline", "champion",
                "contender", "training", "camp",
            ],
            "Fighter Roster": [
                "roster", "fighter", "create a fighter", "caf", "likeness",
                "dlc fighter", "update roster",
            ],
            "Online / Ranked": [
                "online", "ranked", "matchmaking", "division", "ultimate team",
                "pvp", "versus", "quick fight",
            ],
            "Servers / Performance": [
                "server", "servers", "lag", "latency", "disconnect",
                "fps", "crash", "frame rate", "input delay",
            ],
            "Graphics / Presentation": [
                "graphics", "visuals", "animation", "walkout",
                "arena", "crowd", "commentary", "replay",
            ],
            "Controls / Gameplay Feel": [
                "controls", "stamina", "pacing", "balance", "nerf",
                "buff", "patch", "gameplay", "mechanics",
            ],
        },
    },
    "F1": {
        "name": "F1",
        "full_name": "F1 26",
        "publisher": "EA Sports",
        "icon": "",
        "genre": "racing / Formula 1",
        "community_noun": "fans",
        "compare_hint": "e.g., F1 25 launch",
        "ai_context": "the video game F1 26 by EA Sports (Formula 1 racing)",
        "chatbot_role": "an F1 26 community data analyst",
        "topic_buckets": {
            "Handling / Physics": [
                "handling", "physics", "grip", "tyre", "tire", "oversteer",
                "understeer", "braking", "traction", "downforce",
            ],
            "Career / MyTeam": [
                "career", "my team", "myteam", "driver career", "create team",
                "regulation changes", "r&d", "development",
            ],
            "Online / Multiplayer": [
                "online", "multiplayer", "ranked", "matchmaking", "lobby",
                "league", "co-op", "social play",
            ],
            "Tracks / Circuits": [
                "track", "circuit", "spa", "monza", "silverstone", "monaco",
                "las vegas", "suzuka", "new track", "layout",
            ],
            "AI Difficulty": [
                "ai", "difficulty", "ai difficulty", "easy", "hard",
                "adaptive", "overtake", "defend", "rubber banding",
            ],
            "Servers / Performance": [
                "server", "servers", "lag", "latency", "disconnect",
                "fps", "crash", "frame rate", "input delay",
            ],
            "Graphics / Presentation": [
                "graphics", "visuals", "weather", "rain", "night race",
                "replay", "broadcast", "commentary", "hud",
            ],
            "Strategy / Pit Stops": [
                "strategy", "pit stop", "pit", "undercut", "overcut",
                "tyre strategy", "safety car", "vsc", "drs",
            ],
        },
    },
}

DEFAULT_TITLE = "NHL"


def get_title_config(title_key=None):
    if title_key is None:
        import streamlit as st
        title_key = st.session_state.get("active_title", DEFAULT_TITLE)
    return TITLES.get(title_key, TITLES[DEFAULT_TITLE])
