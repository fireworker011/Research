#!/usr/bin/env python3
"""Write minimaxh3/episodes/futanari-rei-escape/episode.json from the cut pack."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "minimaxh3" / "episodes" / "futanari-rei-escape" / "episode.json"

REI_LOCK = (
    "21-year-old Japanese beauty, long straight brown hair, slender body, narrow waist, "
    "C-cup breasts, futanari, FULLY NUDE bare skin, no fabric, no denim, no jacket, no skirt, "
    "no shoes, no socks, bare feet, fully erect 24cm penis that is her own photorealistic human flesh "
    "attached at the groin, skin-colored, not a toy, not plastic, not neon pink, always visible even after ejaculation. "
    "Visible sweat beads and smeared grimy brown dirt all over the body, on the face, breasts, belly, back, arms, "
    "thighs, legs, feet, and the fully erect 24cm penis. Damp dirty hair stuck to the forehead. "
    "The sweat and dirt stay readable on the skin and on the shaft. "
    "Default face: mouth closed or barely open, lips together, tongue fully inside the mouth and hidden, "
    "eyes open looking forward, flushed cheeks only. NOT an orgasm face. NOT ahegao. Tongue out ONLY when the action "
    "says climax or the circular snout is milking her. Protagonist name is Rei only. Do not replace Rei with a male body. "
    "The 24cm penis does not disappear after climax"
)
REI_LOCK_GONE = (
    "21-year-old Japanese beauty, long straight brown hair, slender body, narrow waist, "
    "C-cup breasts, FULLY NUDE bare skin, no fabric, no denim, no jacket, no skirt, "
    "no shoes, no socks, bare feet. No penis. The grown shaft is gone. Only a hairless slit at the groin. "
    "Visible sweat beads and smeared grimy brown dirt all over the body, on the face, breasts, belly, back, arms, "
    "thighs, legs, feet, and the hairless slit. Damp dirty hair stuck to the forehead. "
    "The sweat and dirt stay readable on the skin. "
    "Default face: mouth closed or barely open, lips together, tongue fully inside the mouth and hidden, "
    "eyes open looking forward, flushed cheeks only. NOT an orgasm face. NOT ahegao. "
    "Protagonist name is Rei only. Do not replace Rei with a male body"
)
BEAST_LOCK = (
    "aberrant circular maw growing from a ruined castle stone column and a dead fireplace, "
    "body mass twice Rei's height, wet stone-gray lumpy flesh, a PUCKERED hypotoco-like snout: "
    "the circular oral disc is NARROWED and cinched like pursed fleshy lips, wrinkled bunched outer rim, "
    "NOT a huge wide funnel, NOT a camera-iris gape, white triangular teeth pointing inward stay tucked "
    "behind the cinched rim, wet inner tunnel, slime drooling from the puckered maw, "
    "NO human face, NO human hands, NO human lips, NO human jaw"
)
MOTH_LOCK = (
    "spider-woman the same height as Rei: attractive flushed human female face, brown hair, "
    "nude beautiful human female torso with breasts exposed, human female shoulders. "
    "Lower body stays arachnid: segmented spider abdomen instead of a human pelvis, "
    "many thin spider legs for locomotion (not a pair of human thighs), a tapering tail coming from the REAR "
    "of the spider abdomen. The terminal TIP of that tail has a wet circular second mouth. "
    "Ruined gothic castle hall only, NO forest background, NO trees, NO dirt path, NO human hips, NO human thighs"
)
SUCC_LOCK = (
    "succubus, long black hair, glowing red eyes, two black curved horns, crimson facial markings, "
    "black choker and thin chain necklace, huge tattered bat wings with pink-red cracked membranes "
    "and black torn edges with holes, long thin tail, dark organic markings on the arms as skin, "
    "long claws on the fingers, clawed feet, dark spiked scale texture on the lower legs as skin, "
    "slender waist, modest-to-full breasts, fully nude bare skin, hairless vulva, exposed breasts "
    "and slit, wings remain, horns remain, choker remains, face marks remain, hand claws remain, "
    "foot claws remain, photorealistic"
)
SUCC_GROWN = (
    SUCC_LOCK
    + " penis growth, an erect 24cm penis of her own photorealistic human flesh at the groin, "
    "skin-colored, not a toy, not plastic, not neon pink"
)
WORLD = (
    "photorealistic side-scrolling ruined gothic castle, stone hall with pointed windows and a stone staircase "
    "on the right for standing and encounters, vaulted stone corridor with holes in the ceiling for runs, "
    "aged stone, wall hangings stay attached to the stone, rim lighting, 16:9 locked side view, floor LEFT to RIGHT"
)
CAM = (
    "Locked side-on 2D side-scroller third-person gameplay camera at hip-to-shoulder height. "
    "PROFILE view: the floor runs LEFT to RIGHT across the frame. Adults move LEFT or RIGHT. "
    "Everyone in frame stays full body including feet. The camera stays in the side plane"
)
HALL = (
    "ruined gothic castle hall, pointed stone windows, stone staircase on the right, wall hangings on the stone"
)
VAULT = "vaulted stone corridor in the ruined gothic castle, holes in the ceiling, wall hangings on the stone"
PLACE = HALL
POSE_BAN = (
    "no arm, elbow, or hand entering the vagina; the only thing inside is the 24cm penis. "
    "Do not start the in-and-out until the shaft is buried to the base. The succubus does not walk "
    "away. Do not pack kiss-to-creampie into one clip. Fully nude succubus, keep wings, horns, "
    "choker, and claws. Only these two. Feet planted. Background does not scroll"
)
FACE_REST = (
    "Rei's mouth closed or barely open, tongue fully inside the mouth and hidden, eyes open, flushed cheeks only, "
    "not an orgasm face"
)
FACE_ORGASM = "Rei orgasm face: tongue out, drool, runny nose, trembling"
NUDE = "Rei fully nude bare skin, no fabric anywhere, bare feet, 24cm penis is her own human flesh attached at the groin"
NUDE_AFTER = (
    "Rei fully nude bare skin, no fabric anywhere, bare feet. No penis. The grown shaft is gone. "
    "Sweat beads and grimy brown dirt stay readable on her skin"
)
GONE_LOCK = {"rei": REI_LOCK_GONE}
GROWN_LOCK = {"rei": REI_LOCK_GONE, "succubus": SUCC_GROWN}


def hud(stage: str, *, complete: bool = False, hint: str = "汚れなし") -> dict:
    return {
        "mission": "異形の体内から脱出",
        "mission_keyword": "脱出",
        "hint": hint,
        "health": 1.0,
        "stamina": 1.0,
        "money": "0",
        "heat": 0,
        "objective_bearing": 90,
        "objective_distance": 0.4 if stage != "EXIT" else 0.05,
        "icons_active": ["走"],
        "complete": complete,
    }


def voices(*lines: str, who: str = "rei") -> list[dict]:
    return [{"who": who, "line": line} for line in lines]


def beat(
    bid: str,
    action: str,
    *,
    cast: list[str] | None = None,
    seconds: float = 6.0,
    extra: list | None = None,
    voice: tuple[str, ...] = ("はあ",),
    slot: str | None = None,
    overlays: dict | None = None,
    stage: str = "01",
    cut: bool = False,
    loco: str | None = None,
    place: str | None = None,
    cast_lock: dict | None = None,
) -> dict:
    out: dict = {
        "id": bid,
        "source": "t2v",
        "camera_pack": "none",
        "trim": {"start": 0, "seconds": seconds},
        "cast": list(cast or ["rei"]),
        "face_visible": False,
        "props": [],
        "place": place or PLACE,
        "camera": CAM,
        "action": action,
        "voices": voices(*voice),
        "sfx": "Stone hall ambience, footsteps on stone, heavy breathing",
        "music": "Low pulsing synth bass with a sparse taiko hit at the start; holds under the whole clip.",
        "hud": hud(stage),
    }
    if cut:
        # New encounter / new set piece is T2V even when CONNECT is chain.
        # Vanish-run is NOT locked: chain mode fades the previous body from the last frame.
        out["connect"] = "t2v"
    if loco:
        out["loco"] = loco
    if cast_lock:
        out["cast_lock"] = cast_lock
    if extra is not None:
        out["extra_loras"] = extra
    if slot:
        out["rei_slot"] = slot
    if overlays:
        out.update(overlays)
    return out


def ov(action: str, **kwargs: object) -> dict:
    extra = kwargs.pop("extra", None)
    voice = kwargs.pop("voice", None)
    bid = kwargs.pop("id", None)
    cast = kwargs.pop("cast", None)
    seconds = kwargs.pop("seconds", None)
    loco = kwargs.pop("loco", None)
    out: dict = {"action": action}
    if extra is not None:
        out["extra_loras"] = extra
    if voice is not None:
        out["voices"] = voices(*voice) if isinstance(voice, tuple) else voice
    if bid:
        out["id"] = bid
    if cast is not None:
        out["cast"] = cast
    if seconds is not None:
        out["trim"] = {"start": 0, "seconds": seconds}
    if loco is not None:
        out["loco"] = loco
    out.update(kwargs)
    return out


def hazard(bid: str, action: str, stage: str) -> dict:
    return beat(
        bid,
        action,
        seconds=6.0,
        extra=["mystic"],
        voice=("んっ", "はあ"),
        stage=stage,
        cut=True,
        loco="planted",
    )


def _pair(insert: str, piston: str, in_id: str, out_id: str) -> list[dict]:
    return [
        ov(insert, id=in_id, cast=["rei", "succubus"], seconds=8.0, voice=("はあ", "んっ"), loco="planted", cast_lock=GROWN_LOCK),
        ov(piston, id=out_id, cast=["rei", "succubus"], seconds=8.0, voice=("いく", "はあ"), loco="planted", cast_lock=GROWN_LOCK),
    ]


def pose_fours() -> list[dict]:
    insert = (
        f"{POSE_BAN}. {NUDE_AFTER}. side view, Rei on palms and knees on the stone hall floor facing right, "
        "NOT walking, knees and feet planted. The succubus kneels still behind her, feet planted, and pushes her own "
        "erect 24cm penis into Rei's hairless slit from behind until the base meets Rei's hips, HOLD, no piston yet. "
        f"Clawed hands planted. Wings along the succubus back. Sweat and dirt stay on Rei. {FACE_REST}"
    )
    piston = (
        f"{POSE_BAN}. same palms-and-knees side view, both still planted. Only after the succubus shaft is buried "
        f"to the base do her hips move base-to-mid-to-base, then creampie overflow inside Rei, {FACE_ORGASM}. "
        "The grown shaft stays on the succubus. No penis on Rei. Sweat and dirt stay on Rei. No walk-away"
    )
    return _pair(insert, piston, "20-fours-in", "20-fours-out")


def pose_wall() -> list[dict]:
    insert = (
        f"{POSE_BAN}. {NUDE_AFTER}. side view, CAMERA LOCKED, background does not scroll. "
        "Rei STANDING STILL facing the stone wall, PALMS FLAT on the stone wall, fingers spread, knees "
        "slightly bent, bare feet planted, NOT walking, NOT striding, NOT tiptoe-walking. "
        "The succubus STANDING STILL behind her, clawed feet planted, wings up, hips against Rei's hips. "
        "The succubus's erect 24cm penis ENTERS Rei's hairless slit from behind and the entire shaft slides in "
        "until the base meets Rei's buttocks and HOLDS. "
        "The penis is INSIDE the vagina. The shaft is surrounded by the slit. The tip is not on the far side of a thigh. "
        f"No piston yet. No penis on Rei. Sweat and dirt stay on Rei. {FACE_REST}"
    )
    piston = (
        f"{POSE_BAN}. same standing side view, CAMERA LOCKED, Rei's palms still flat on the wall, both still planted, "
        f"the succubus moves in-and-out to the hilt then creampie overflow from Rei's slit down her thighs, {FACE_ORGASM}, "
        "the succubus does not walk away, her penis stays inside until pullout, never through the thigh. "
        "No penis on Rei. Sweat and dirt stay on Rei"
    )
    return _pair(insert, piston, "20-wall-in", "20-wall-out")


def pose_over() -> list[dict]:
    ride = (
        f"{POSE_BAN}. {NUDE_AFTER}. side view, CAMERA LOCKED. Rei lies on her back on the stone hall floor, not walking, "
        "knees open. The succubus kneels over Rei's hips and sinks her own erect 24cm penis into Rei's hairless slit "
        "until the base meets Rei, HOLD, then her hips rise until mid-shaft shows and drop until the base meets Rei, "
        f"repeat. Wings open for balance. Claws on Rei's chest. Rei holds still. Sweat and dirt stay on Rei. {FACE_REST}"
    )
    cream = (
        f"{POSE_BAN}. same bodies, last drops go to the hilt and hold, creampie overflow from Rei's slit around the "
        f"buried base, succubus mouth open, {FACE_ORGASM}. "
        "The grown shaft stays on the succubus when she lifts off. No penis on Rei. Sweat and dirt stay on Rei. Wings still in frame"
    )
    return _pair(ride, cream, "20-straddle-ride", "20-straddle-out")


def pose_supine() -> list[dict]:
    insert = (
        f"{POSE_BAN}. {NUDE_AFTER}. side view, CAMERA LOCKED. Rei on her back on the stone hall floor, knees "
        "open, not walking. The succubus kneels still between Rei's legs, wings spread, and places the head of her own "
        "erect 24cm penis at Rei's hairless slit, then pushes until the entire shaft is buried to the base and STOPS. "
        f"No thrusting yet. Claws on Rei's shoulders. Sweat and dirt stay on Rei. {FACE_REST}"
    )
    piston = (
        f"{POSE_BAN}. same bodies, same side-view angle, only after the succubus shaft is already buried do her hips "
        "start an in-and-out: pull out to mid-shaft then slam back to the base, repeat, then creampie overflow inside Rei, "
        f"{FACE_ORGASM}. No penis on Rei. The grown shaft stays on the succubus. Sweat and dirt stay on Rei"
    )
    return _pair(insert, piston, "20-supine-in", "20-supine-out")


pose_straddle = pose_over


def build() -> dict:
    s05 = (
        f"Only Rei and this one beast. 16:9 side view. CAMERA LOCKED. {NUDE}. Rei STANDING STILL on the left in the castle hall, feet planted, "
        f"NOT walking, {FACE_REST}. An aberrant circular maw grows from a ruined stone column and a dead fireplace, body mass twice Rei's height. "
        "From the column the PUCKERED hypotoco-like snout turns toward Rei's groin: the circular oral disc is NARROWED and "
        "cinched like pursed fleshy lips, wrinkled bunched rim, NOT a huge wide funnel, NOT a camera-iris gape. "
        "The small cinched opening slides FORWARD over the 24cm penis until the puckered rim SEALS at the base. "
        "The entire shaft disappears inside. Outer stone-gray snout flesh bunches around the root. Then continue without a cut: "
        "the outer rim STAYS CINCHED at the base. Motion is NOT a human head bob and NOT a jaw chew and NOT a big maw pumping. "
        "Inner wall PERISTALSIS only: concentric rings contract root-to-tip-to-root about 8 to 12cm while the outer hypotoco rim "
        "does not break the seal. While it milks her, her mouth may open and her tongue may come out from the pleasure. "
        f"At second 5 she climaxes: {FACE_ORGASM}. Thick ejaculation pumps into the gullet. Overflow drips from the cinched rim. "
        "Do not shrink the beast. Do not grow a human face. Keep the snout puckered and small on the shaft"
    )
    s05_invite = (
        f"Only Rei and this one beast. 16:9 side view. CAMERA LOCKED. {NUDE}. Rei lies on her back on the stone hall floor, "
        f"smiling with mouth closed, tongue inside, knees open thighs apart, 24cm erect pointing up, NOT walking, {FACE_REST}. "
        "The circular maw stays on the stone column and dead fireplace beside her, body mass twice Rei's height. "
        "The PUCKERED hypotoco-like snout turns DOWN onto Rei's groin: circular oral disc NARROWED and cinched like pursed fleshy lips, "
        "NOT a huge wide funnel. The small cinched opening slides DOWN over the 24cm penis until the puckered rim SEALS at the base. "
        "The entire shaft disappears inside. Then continue without a cut: outer rim STAYS CINCHED at the base. "
        "NOT a head bob. Inner PERISTALSIS only, 8 to 12cm along the shaft. While it milks her, tongue may come out from the pleasure. "
        f"At second 5 she climaxes: {FACE_ORGASM}, still on her back, still smiling through it. Thick ejaculation into the gullet. "
        "Do not shrink the beast. Do not grow a human face. Keep the snout puckered. Rei stays on her back with knees open"
    )
    s06_after = (
        f"The column maw completely fades out of frame, no walk-away, no residual snout. "
        f"{NUDE}. Rei's mouth closes, tongue retracts fully inside, not an orgasm face anymore. "
        "Then she sprints left to right through the vaulted stone corridor, 24cm bouncing after ejaculation, no extra people"
    )
    s06_up = (
        f"The column maw completely fades out of frame, no walk-away, no residual snout. "
        f"{NUDE}. Rei pushes up off her back onto her feet. Mouth closes, tongue retracts fully inside, not an orgasm face anymore. "
        "Then she sprints left to right through the vaulted stone corridor, 24cm bouncing after ejaculation, no extra people"
    )
    s06_evade = (
        f"The column maw lunges once and misses. Rei ducks aside and the maw "
        f"completely fades out of frame, no walk-away, no residual snout. {NUDE}. "
        f"Rei untouched and not yet climaxed, {FACE_REST}, then she sprints left to right, no extra people"
    )
    moth_tail = (
        f"Only Rei and this one spider-woman. CAMERA LOCKED. {NUDE}. Rei STANDING STILL, feet planted, NOT walking, NOT bouncing in place, "
        f"{FACE_REST}. The spider-woman STANDING STILL. The orifice at the TIP of the tail (coming from the REAR of the spider abdomen) "
        "is a SECOND MOUTH, not a human vulva, not between human thighs. "
        "The segmented spider abdomen curls, the tail hooks under toward Rei's groin. The wet circular opening at the tail tip "
        "cinches and slides onto the 24cm shaft until the tail-mouth SEALS at the base. Inner tail-throat PERISTALSIS: rings of "
        "flesh contract root-to-tip along the buried shaft. Human upper body holds Rei. Extra spider legs brace on the stone floor. "
        "No human pelvis. No human thighs. While it milks her, tongue may come out. "
        f"Then climax: {FACE_ORGASM}, thick ejaculation into the tail-throat, overflow at the sealed tail-rim. 24cm stays erect after"
    )
    moth_mouth = (
        f"Only Rei and this one spider-woman. CAMERA LOCKED. {NUDE}. Both STANDING STILL, feet planted, NOT walking. "
        "Spider-woman's HUMAN upper face leans in. Spider abdomen and extra "
        "legs remain visible behind her. She does not grow human thighs. Her human lips part and slide down the 24cm shaft until "
        f"they reach the base. Tongue on the underside. The spider tail hangs unused. {FACE_REST} until the last seconds, then {FACE_ORGASM}"
    )
    beats = [
        beat(
            "01-open-stroke",
            f"side view 16:9, CAMERA LOCKED. {NUDE}. Rei STANDING STILL in the ruined gothic castle hall, NOT running, NOT walking, "
            f"feet planted, knees slightly bent, both hands sliding along her fully erect 24cm penis from base to head repeatedly, "
            f"grip traveling the full 24cm, {FACE_REST}, stone floor, pointed windows, staircase on the right. "
            "Do not ejaculate in this clip. Do not start running in this clip",
            seconds=8.0,
            voice=("はあ", "んっ"),
            stage="01",
            loco="planted",
        ),
        beat(
            "02-run-a",
            f"side-scrolling runner shot, {NUDE}, {FACE_REST}, Rei sprinting left to right through the vaulted stone corridor, "
            "long brown hair flowing, erect 24cm penis bouncing with each stride, holes in the ceiling, no enemy in frame",
            seconds=6.0,
            voice=("はあ",),
            stage="01",
            loco="run",
            place=VAULT,
        ),
        hazard(
            "03-slime",
            f"side view 16:9, CAMERA LOCKED. {NUDE}. Rei STANDING STILL, feet planted, NOT walking, {FACE_REST}. "
            "A translucent slime mass the size of her torso rises from the stone floor, no human face, no hands. "
            "A circular mouth in the slime seals over her fully erect 24cm penis to the base and milks with slow inner pulses. "
            "Sweat and dirt stay on her skin. Then the slime collapses and is gone. Only Rei remains",
            "01",
        ),
        beat(
            "04-enemy1",
            f"side view 16:9 encounter, CAMERA LOCKED. {NUDE}. Rei STANDING STILL on the left facing right, feet planted, NOT walking, "
            f"{FACE_REST}. An aberrant circular maw, body mass twice Rei's height, emerges from the stone column and dead fireplace on the right, "
            "PUCKERED hypotoco snout cinched small, slime drooling, NO human face, NO human hands, NO human lips, NO human jaw, "
            "brief pause, only Rei plus this one beast",
            cast=["rei", "beast"],
            seconds=6.0,
            extra=["mystic"],
            voice=("はあ",),
            stage="01",
            cut=True,
            loco="planted",
        ),
        beat(
            "05-enemy1-maw",
            s05,
            cast=["rei", "beast"],
            seconds=10.0,
            extra=["mystic"],
            voice=("んっ", "いく"),
            slot="beast",
            stage="01",
            loco="planted",
            overlays={
                "rei_beast_accept": ov(
                    s05,
                    id="05-enemy1-maw",
                    extra=["mystic"],
                    seconds=10.0,
                    voice=("んっ", "いく"),
                    cast=["rei", "beast"],
                    loco="planted",
                ),
                "rei_beast_invite": ov(
                    s05_invite,
                    id="05-enemy1-invite",
                    extra=["mystic"],
                    seconds=10.0,
                    voice=("んっ", "いく"),
                    cast=["rei", "beast"],
                    loco="planted",
                ),
            },
        ),
        beat(
            "06-fade-run-b",
            s06_after,
            seconds=6.0,
            voice=("はあ",),
            slot="beast",
            stage="01",
            loco="run",
            place=VAULT,
            overlays={
                "rei_beast_accept": ov(s06_after, id="06-fade-run-b", seconds=6.0, voice=("はあ",), loco="run"),
                "rei_beast_invite": ov(s06_up, id="06-fade-run-b", seconds=6.0, voice=("はあ",), loco="run"),
                "rei_beast_evade": ov(s06_evade, id="06-fade-run-b", seconds=6.0, voice=("はあ",), loco="run"),
            },
        ),
        hazard(
            "07-hearth",
            f"side view 16:9, CAMERA LOCKED. {NUDE}. Rei STANDING STILL in front of the dead fireplace, feet planted, "
            f"NOT walking, {FACE_REST}. The hearth mouth is a stone-gray circular opening, not a human face. "
            "It slides over her fully erect 24cm penis to the base and the inner stone throat pulses. "
            "Sweat and dirt stay on her skin. Then the hearth mouth releases and she is alone",
            "01",
        ),
        beat(
            "08-toilet",
            f"side view 16:9, CAMERA LOCKED. {NUDE}. Rei STANDING STILL on the left, feet planted, NOT walking, {FACE_REST}, "
            "facing a carnivorous-plant seat grown in the castle hall: green outer rind, wet inner bowl, "
            "nectar-colored liquid in the bowl, plant flesh formed like a western seat, NOT ceramic, NOT porcelain, NOT a bathtub, "
            "no other people, brief pause",
            seconds=6.0,
            voice=("んっ",),
            stage="02",
            cut=True,
            loco="planted",
        ),
        beat(
            "09-toilet-act",
            f"side view, CAMERA LOCKED. {NUDE}. Rei SITTING STILL on a carnivorous-plant seat, "
            f"green outer rind, wet inner bowl, nectar-colored liquid, NOT ceramic, both hands sliding the 24cm penis base-to-head until thick ejaculation arcs, "
            f"{FACE_REST} until climax then {FACE_ORGASM}, only Rei in frame, then the toilet shape fades",
            seconds=8.0,
            voice=("いく", "はあ"),
            slot="toilet",
            stage="02",
            loco="planted",
            overlays={
                "rei_toilet_ta": ov(
                    f"side view, CAMERA LOCKED. {NUDE}. Rei SITTING STILL on a carnivorous-plant seat, "
                    f"green outer rind, wet inner bowl, nectar-colored liquid, NOT ceramic, both hands sliding the 24cm penis base-to-head until thick ejaculation arcs, "
                    f"{FACE_REST} until climax then {FACE_ORGASM}, only Rei in frame, then the toilet shape fades",
                    id="09-ta",
                    seconds=8.0,
                    voice=("いく", "はあ"),
                    loco="planted",
                ),
                "rei_toilet_tb": ov(
                    f"side view, CAMERA LOCKED. {NUDE}. Rei SITTING STILL on the same carnivorous-plant seat, NOT ceramic, "
                    f"a visible urine stream leaving the erect 24cm penis into the nectar-colored bowl, {FACE_REST}, only Rei in frame, then the plant seat fades",
                    id="09-tb",
                    seconds=8.0,
                    voice=("んっ", "はあ"),
                    loco="planted",
                ),
                "rei_toilet_tc": ov(
                    f"side view, CAMERA LOCKED. {NUDE}. Rei STANDING STILL, feet planted, NOT walking, {FACE_REST}. "
                    "From the carnivorous-plant seat, a wet tentacle grows and the circular puckered mouth at the tentacle tip "
                    "slides onto the 24cm penis until the rim SEALS at the base. Inner tentacle-throat PERISTALSIS milks root-to-tip. "
                    f"NOT a human mouth. Green rind and nectar-colored liquid only. While it milks her, tongue may come out. Then {FACE_ORGASM}, thick ejaculation into the tentacle. "
                    "Only Rei plus the tentacles. Then they fade",
                    id="09-tc",
                    extra=["mystic"],
                    seconds=8.0,
                    voice=("んっ", "はあ"),
                    loco="planted",
                ),
            },
        ),
        beat(
            "10-run-c",
            f"side-scrolling runner shot, {NUDE}, {FACE_REST}, Rei sprinting left to right through the vaulted stone corridor, "
            "long brown hair flowing, erect 24cm penis bouncing, no enemy in frame, sweat and dirt stay on her skin",
            seconds=6.0,
            voice=("はあ",),
            stage="02",
            loco="run",
            place=VAULT,
        ),
        hazard(
            "11-leech",
            f"side view 16:9, CAMERA LOCKED. {NUDE}. Rei STANDING STILL, feet planted, NOT walking, {FACE_REST}. "
            "A thick leech, no face, no hands, clamps its round mouth on her fully erect 24cm penis and stays sealed "
            "at the base while its body pulses. Sweat and dirt stay on her skin. Then the leech drops off and is gone",
            "02",
        ),
        beat(
            "12-moth",
            f"side view encounter, CAMERA LOCKED. {NUDE}. Rei STANDING STILL, feet planted, NOT walking, {FACE_REST}. "
            "Spider-woman standing in the castle hall on the right, same height as Rei, attractive flushed human female face, "
            "brown hair, nude beautiful human female torso, "
            "lower body stays arachnid: segmented spider abdomen, many thin spider legs, "
            "tapering tail from the REAR with a wet circular second mouth at the TIP, ruined gothic castle hall only, "
            "only Rei plus this one spider-woman, both still, brief pause",
            cast=["rei", "moth"],
            seconds=6.0,
            extra=["mystic"],
            voice=("はあ",),
            stage="03",
            cut=True,
            loco="planted",
        ),
        beat(
            "13-moth-act",
            moth_tail,
            cast=["rei", "moth"],
            seconds=10.0,
            extra=["mystic"],
            voice=("んっ", "いく"),
            slot="moth",
            stage="03",
            loco="planted",
            overlays={
                "rei_moth_tail": ov(moth_tail, id="13-tail", extra=["mystic"], seconds=10.0, voice=("んっ", "いく"), cast=["rei", "moth"], loco="planted"),
                "rei_moth_mouth": ov(moth_mouth, id="13-mouth", extra=["blowjob"], seconds=10.0, voice=("んっ", "いく"), cast=["rei", "moth"], loco="planted"),
            },
        ),
        beat(
            "14-fade-run-d",
            f"The spider-woman completely fades out of frame, no walk-away, no residual spider leg or tail. "
            f"{NUDE}. Mouth closes, tongue retracts, {FACE_REST}. Then she sprints left to right through the vaulted stone corridor, "
            "24cm bouncing, no extra people",
            seconds=6.0,
            voice=("はあ",),
            stage="03",
            loco="run",
            place=VAULT,
        ),
        hazard(
            "15-tentacles",
            f"side view 16:9, CAMERA LOCKED. {NUDE}. Rei STANDING STILL, feet planted, NOT walking, {FACE_REST}. "
            "Wet tentacles rise from a crack in the stone floor, no human face. One circular mouth seals on her "
            "fully erect 24cm penis to the base and pulses. Sweat and dirt stay on her skin. "
            "Then the tentacles withdraw into the crack",
            "03",
        ),
        beat(
            "16-succ",
            f"side view 16:9, CAMERA LOCKED. {NUDE}. Rei STANDING STILL, feet planted, NOT walking, {FACE_REST}. "
            "Succubus stands in from the right of the castle hall, fully nude bare skin, hairless vulva, exposed breasts and slit, "
            "wings remain, horns remain, choker remains, face marks remain, hand claws remain, foot claws remain, "
            "obsessed expression, reaching toward Rei but not touching yet. The fully erect 24cm penis is still Rei's, "
            "still attached at Rei's groin. Just before contact. Only Rei plus this one succubus, both still, brief pause. "
            "Sweat and dirt stay on Rei",
            cast=["rei", "succubus"],
            seconds=6.0,
            voice=("はあ",),
            stage="04",
            cut=True,
            loco="planted",
        ),
        beat(
            "17-attack",
            f"side view, CAMERA LOCKED, background does not scroll. {NUDE}. Both STANDING STILL, feet planted, NOT walking. "
            "They touch. Futanari transformation. penis growth. Rei's fully erect 24cm penis shrinks away until it is gone "
            "and only a hairless slit remains. The succubus grows an erect 24cm penis of her own flesh at the groin, "
            "penis growth, from nothing to the full 24cm. Wings, horns, choker, and claws stay. "
            f"Sweat and dirt stay on Rei. Only these two. {FACE_REST}",
            cast=["rei", "succubus"],
            seconds=8.0,
            extra=["futatf"],
            voice=("んっ", "はあ"),
            stage="04",
            loco="planted",
            cast_lock={"succubus": SUCC_GROWN},
        ),
        beat(
            "18-kiss",
            f"side view, CAMERA LOCKED. {NUDE_AFTER}. Frontal embrace. Both STANDING STILL, feet planted, NOT walking. "
            "They kiss passionately. Both tongues visible inside the open mouths, saliva string, succubus red eyes "
            "half-lidded, horns and choker in frame, torn wings behind. The succubus's erect 24cm stays on her. "
            "No penis on Rei. Sweat and dirt stay on Rei. Only these two",
            cast=["rei", "succubus"],
            seconds=6.0,
            extra=["kiss"],
            voice=("んっ",),
            slot="kiss",
            stage="04",
            loco="planted",
            cast_lock=GROWN_LOCK,
            overlays={
                "rei_kiss_on": ov(
                    f"side view, CAMERA LOCKED. {NUDE_AFTER}. Frontal embrace. Both STANDING STILL, feet planted, NOT walking. "
                    "They kiss passionately. Both tongues visible inside the open mouths, saliva string, succubus red eyes "
                    "half-lidded, horns and choker in frame, torn wings behind. The succubus's erect 24cm stays on her. "
                    "No penis on Rei. Sweat and dirt stay on Rei. Only these two",
                    id="18-kiss",
                    extra=["kiss"],
                    cast=["rei", "succubus"],
                    loco="planted",
                    cast_lock=GROWN_LOCK,
                ),
            },
        ),
        beat(
            "19-oral",
            f"CAMERA LOCKED. {NUDE_AFTER}. The succubus STANDING STILL, feet planted, her erect 24cm pointing forward, "
            "wings folded, horns and choker stay. Rei squats with thighs spread, feet planted, NOT walking. "
            "Rei's lips travel the succubus 24cm from the head to the base and back, several full passes. "
            "One of Rei's hands stays on her own hairless slit. The other hand travels from the succubus thigh up to the waist. "
            f"No penis on Rei. Sweat and dirt stay on Rei. {FACE_REST} until the last seconds. Only these two",
            cast=["rei", "succubus"],
            seconds=8.0,
            extra=["blowjob"],
            voice=("んっ", "はあ"),
            slot="oral",
            stage="04",
            loco="planted",
            cast_lock=GROWN_LOCK,
            overlays={
                "rei_oral_on": ov(
                    f"CAMERA LOCKED. {NUDE_AFTER}. The succubus STANDING STILL, feet planted, her erect 24cm pointing forward, "
                    "wings folded, horns and choker stay. Rei squats with thighs spread, feet planted, NOT walking. "
                    "Rei's lips travel the succubus 24cm from the head to the base and back, several full passes. "
                    "One of Rei's hands stays on her own hairless slit. The other hand travels from the succubus thigh up to the waist. "
                    f"No penis on Rei. Sweat and dirt stay on Rei. {FACE_REST} until the last seconds. Only these two",
                    id="19-oral",
                    extra=["blowjob"],
                    seconds=8.0,
                    voice=("んっ", "はあ"),
                    cast=["rei", "succubus"],
                    loco="planted",
                    cast_lock=GROWN_LOCK,
                ),
            },
        ),
        beat(
            "20-pose",
            pose_fours()[0]["action"],
            cast=["rei", "succubus"],
            seconds=8.0,
            voice=("はあ", "んっ"),
            slot="pose",
            stage="04",
            loco="planted",
            cast_lock=GROWN_LOCK,
            overlays={
                "rei_pose_fours": pose_fours(),
                "rei_pose_wall": pose_wall(),
                "rei_pose_straddle": pose_straddle(),
                "rei_pose_supine": pose_supine(),
            },
        ),
        beat(
            "21-orgasm",
            f"side view, CAMERA LOCKED. {NUDE_AFTER}. Both still, NOT walking. {FACE_ORGASM}. "
            "The succubus's erect 24cm is still buried in Rei's hairless slit. Visible creampie overflow from Rei's slit. "
            "No penis on Rei. The grown shaft is gone from Rei and stays on the succubus. "
            "Sweat and dirt stay on Rei. Wings, horns, choker, and claws stay on the succubus. No extra people",
            cast=["rei", "succubus"],
            seconds=8.0,
            voice=("いく", "はあ"),
            stage="04",
            loco="planted",
            cast_lock=GROWN_LOCK,
        ),
        beat(
            "22-succ-fade",
            f"succubus fades completely out of frame, no walk-away, no residual wing or tail or horn. {NUDE_AFTER}. "
            f"No penis. The grown shaft is gone. Sweat beads and grimy brown dirt stay readable on her skin. "
            f"Mouth closes, tongue retracts, {FACE_REST}. Then she starts running right through the vaulted stone corridor",
            seconds=6.0,
            voice=("はあ",),
            stage="04",
            loco="run",
            place=VAULT,
            cast_lock=GONE_LOCK,
        ),
        beat(
            "23-run-e",
            f"side-scrolling runner shot, {NUDE_AFTER}, {FACE_REST}, Rei sprinting left to right toward a bright tear of light "
            "at the RIGHT end of the vaulted stone corridor, no enemy. No penis. The grown shaft is gone. "
            "Sweat beads and grimy brown dirt stay readable on her skin",
            seconds=6.0,
            voice=("はあ",),
            stage="04",
            loco="run",
            place=VAULT,
            cast_lock=GONE_LOCK,
        ),
        beat(
            "24-escape",
            f"side-scrolling exit, {NUDE_AFTER}, {FACE_REST}, a bright tear of light at the right end of the vaulted stone corridor, "
            "Rei running into the light, leaving the ruined castle. No penis. The grown shaft is gone. "
            "Sweat beads and grimy brown dirt stay readable on her skin. She does not wash",
            seconds=6.0,
            voice=("はあ",),
            stage="EXIT",
            loco="run",
            place=VAULT,
            cast_lock=GONE_LOCK,
        ),
    ]
    beats[-1]["hud"] = hud("EXIT", complete=True)
    return {
        "schema": "h3-episode/v1",
        "slug": "futanari-rei-escape",
        "title": "異形の体内から脱出",
        "subtitle": "架空ゲーム 予告",
        "canvas": "16:9",
        "clip_seconds": 10,
        "tone": "action",
        "render": {
            "preset": "balance",
            "fallback_preset": "speed",
            "seed": 42,
            "lane": "erotic",
            "checkpoint": "eros-max",
            "camera_pack": "side2d",
            "connect": "t2v",
            "voice": "japanese",
            "combat": "off",
            "rei_mast": "skip",
            "rei_toilet": "ta",
            "rei_beast": "accept",
            "rei_moth": "tail",
            "rei_attack": "rei",
            "rei_kiss": "on",
            "rei_oral": "on",
            "rei_pose": "fours",
        },
        "style": (
            "Third-person side-scrolling game cutscene look, live-action photoreal game footage, "
            "pulled-back full-body PROFILE framing, brisk real-time playback, no anime, no illustration"
        ),
        "violence": "none",
        "world": {
            "name": "Ruined gothic castle",
            "lock": WORLD,
            "no_text_on_signs": True,
            "bare_set": False,
        },
        "cast": {
            "rei": {
                "name_ja": "レイ",
                "name_en": "Rei",
                "age": 21,
                "lock": REI_LOCK,
                "voice": "breathy young adult female voice",
            },
            "beast": {
                "name_ja": "異形",
                "name_en": "Beast",
                "age": 21,
                "lock": BEAST_LOCK,
                "voice": "wet inhuman gulp",
            },
            "moth": {
                "name_ja": "蜘蛛女",
                "name_en": "Spider",
                "age": 21,
                "lock": MOTH_LOCK,
                "voice": "soft young adult female voice",
            },
            "succubus": {
                "name_ja": "サキュバス",
                "name_en": "Succubus",
                "age": 24,
                "lock": SUCC_LOCK,
                "voice": "low young adult female voice",
            },
        },
        "props": {},
        "homage": {
            "borrowed": [
                "third-person game camera",
                "pulled-back full-body PROFILE side-on plane, floor LEFT to RIGHT, horizontal track only",
                "mission subtitle grammar with the object noun in colour",
                "a pause-menu command window over a frozen frame",
            ],
            "never": [
                "blowjob",
                "fellatio",
                "doggy",
                "missionary",
                "cowgirl",
                "Aya",
                "Yamada",
                "schoolgirl",
                "sailor",
                "seifuku",
            ],
        },
        "hud": {
            "theme": "bandai",
            "district_label": "体内 Dist.",
            "icons": ["走", "脱", "欲"],
            "complete_text": "ミッション完了",
            "subtitles": True,
            "font": "",
        },
        "cards": {
            "title": True,
            "title_seconds": 2.6,
            "kicker": "舞台・人物・物語はオリジナル",
            "end": True,
            "end_seconds": 3.0,
            "end_title": "異形の体内から脱出",
            "disclaimer": "架空のゲームのコンセプト映像です。実在の製品ではありません。",
            "end_lines": [
                "架空のゲームのコンセプト映像です。実在の製品ではありません。",
                "舞台・人物・物語はオリジナル",
                "成人のみ",
            ],
        },
        "stitch": {
            "transition": "xfade",
            "xfade_s": 0.35,
            "output_height": 720,
            "loudnorm": True,
        },
        "beats": beats,
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    OUT.write_text(blob, encoding="utf-8")
    print("wrote", OUT, "bytes", OUT.stat().st_size, "beats", len(build()["beats"]))


if __name__ == "__main__":
    main()
