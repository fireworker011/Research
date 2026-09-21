#!/usr/bin/env python3
"""Write minimaxh3/episodes/futanari-rei-escape/episode.json from the cut pack."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "minimaxh3" / "episodes" / "futanari-rei-escape" / "episode.json"

REI_LOCK = (
    "21-year-old Japanese beauty, long straight brown hair, slender body, narrow waist, "
    "C-cup breasts, futanari, fully erect 24cm penis always visible even after ejaculation, "
    "photorealistic. Default expression: flushed ecstatic face. Orgasm face: tongue out, drool, "
    "runny nose, trembling. Default clothes: torn damp thin garment half-off, breasts and erect "
    "penis exposed, game-character damaged outfit. Protagonist name is Rei only. Do not replace "
    "Rei with a male body. The 24cm penis does not disappear after climax"
)
BEAST_LOCK = (
    "giant aberrant beast twice Rei's height, pale mint-gray wet lumpy flesh blending into a "
    "pale-gray lamprey-ray hide, circular orange-red oral disc ringed with white triangular teeth "
    "pointing inward, wet red inner funnel, purple lightning veins pulsing under the skin, "
    "lamprey-eel-ray body, membranous pectoral fins, dorsal sucker-stalk with a disc, quadruped "
    "lizard crawl on limb-fins, slime drooling from the circular maw, NO human face, NO human hands, "
    "NO human lips, NO human jaw"
)
MOTH_LOCK = (
    "moth-girl the same height as Rei: attractive flushed human female face, brown hair, curled "
    "ram-like insect antennae on the head, nude beautiful human female torso with breasts exposed, "
    "human female shoulders. Lower body stays insect: segmented moth abdomen instead of a human "
    "pelvis, many thin insect legs for locomotion (not a pair of human thighs), cream moth wings "
    "with purple-gray eyespots, a tapering stinger-like tail. The terminal tip of that tail has a "
    "wet circular orifice. Meat-wall corridor only, NO forest background, NO trees, NO dirt path, "
    "NO human hips"
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
WORLD = (
    "photorealistic side-scrolling interior of a living creature, wet pulsating meat walls, glossy "
    "viscera corridor, springy biological floor that does not sink, humid erotic niku-kabe cave, "
    "rim lighting, 16:9 locked side view, floor LEFT to RIGHT"
)
CAM = (
    "Locked side-on 2D side-scroller third-person gameplay camera at hip-to-shoulder height. "
    "PROFILE view: the floor runs LEFT to RIGHT across the frame. Adults move LEFT or RIGHT. "
    "Everyone in frame stays full body including feet. The camera stays in the side plane and tracks "
    "only left and right on a straight line at brisk walking game speed"
)
PLACE = "living meat-wall viscera corridor, springy biological floor that does not sink"
POSE_BAN = (
    "no arm, elbow, or hand entering the vagina; the only thing inside is the 24cm penis. "
    "Do not start the in-and-out until the shaft is buried to the base. The succubus does not walk "
    "away. Do not pack kiss-to-creampie into one clip. Fully nude succubus, keep wings, horns, "
    "choker, and claws. Only these two"
)


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
) -> dict:
    out: dict = {
        "id": bid,
        "source": "t2v",
        "camera_pack": "none",
        "trim": {"start": 0, "seconds": seconds},
        "cast": list(cast or ["rei"]),
        "face_visible": False,
        "props": [],
        "place": PLACE,
        "camera": CAM,
        "action": action,
        "voices": voices(*voice),
        "sfx": "Wet meat-wall pulse, footsteps on springy viscera, heavy breathing",
        "music": "Low pulsing synth bass with a sparse taiko hit at the start; holds under the whole clip.",
        "hud": hud(stage),
    }
    if cut:
        # Encounter enter / vanish-run stay T2V even when CONNECT is chain,
        # so the previous body does not leak. No second dropdown.
        out["connect"] = "t2v"
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
    out.update(kwargs)
    return out


def mast_pair(prefix: str, stage: str, *, filthy: bool = False) -> dict:
    stand = (
        "side view, Rei standing on the springy meat floor, not running, one or both hands sliding "
        "the fully erect 24cm penis from base to head, grip traveling the full 24cm, hips twitching, "
        "ecstatic flushed face, no enemy in frame"
    )
    back = (
        "side view, Rei lying on her back on the elastic living floor that does not sink, knees up, "
        "one hand sliding the 24cm penis base-to-head, ecstatic face, meat ceiling above, no enemy in frame"
    )
    if filthy:
        stand += ". Filth stains remain as flagged."
        back += ". Filth stains remain as flagged."
    return beat(
        f"{prefix}-mast",
        stand,
        seconds=6.0,
        voice=("んっ", "はあ"),
        slot="mast",
        stage=stage,
        overlays={
            "rei_mast_stand": ov(stand, id=f"{prefix}-mast-stand"),
            "rei_mast_back": ov(back, id=f"{prefix}-mast-back"),
        },
    )


def pose_fours() -> list[dict]:
    insert = (
        f"{POSE_BAN}. side view, succubus on palms and knees on the meat floor facing right, wings "
        "along her back, Rei behind her toward the left, pushes the 24cm in from behind until the "
        "base meets her hips, HOLD, no piston yet, clawed hands planted, clawed feet visible"
    )
    piston = (
        f"{POSE_BAN}. same palms-and-knees side view, hips slam base-to-mid-to-base only after the "
        "hilt is already buried, then creampie overflow, Rei orgasm face tongue out drool runny nose, "
        "succubus looking back, 24cm stays erect after pullout, no walk-away"
    )
    return [
        ov(insert, id="20-fours-in", cast=["rei", "succubus"], seconds=8.0, voice=("はあ", "んっ")),
        ov(piston, id="20-fours-out", cast=["rei", "succubus"], seconds=8.0, voice=("いく", "はあ")),
    ]


def pose_wall() -> list[dict]:
    insert = (
        f"{POSE_BAN}. side view, succubus standing facing right, palms flat on the meat wall, knees "
        "slightly bent, wings up, Rei standing behind her toward the left, pushes in from behind to "
        "the hilt and holds, no piston yet, clawed feet on the springy floor, 24cm buried to the base"
    )
    piston = (
        f"{POSE_BAN}. same standing side view, palms still on the wall, standing in-and-out to the "
        "hilt then creampie overflow down her thighs, both climax faces, Rei tongue out drool runny "
        "nose trembling, 24cm stays erect after pullout, succubus does not walk away"
    )
    return [
        ov(insert, id="20-wall-in", cast=["rei", "succubus"], seconds=8.0, voice=("はあ", "んっ")),
        ov(piston, id="20-wall-out", cast=["rei", "succubus"], seconds=8.0, voice=("いく", "はあ")),
    ]


def pose_straddle() -> list[dict]:
    mouth = (
        f"{POSE_BAN}. side view, open-mouth kiss first, tongues visible, then the succubus lips part "
        "over the 24cm head, travel to the base, hold, pull back to the head, several full passes, "
        "tongue on the underside, wings folded, Rei sitting or on her back on the meat floor, fully nude succubus"
    )
    ride = (
        f"{POSE_BAN}. side view, she rises off the mouth, straddles Rei who lies on the springy meat "
        "floor, sinks until the 24cm is buried to the base, then her hips rise until mid-shaft shows "
        "and drop until the base meets her, repeat, wings open for balance, claws on Rei's chest, "
        "Rei holds still"
    )
    cream = (
        f"{POSE_BAN}. same straddle, last drops go to the hilt and hold, creampie overflow around the "
        "buried base, both climax faces, Rei tongue out drool runny nose trembling, succubus mouth open, "
        "24cm stays erect after she lifts off, wings still in frame"
    )
    return [
        ov(mouth, id="20-straddle-mouth", cast=["rei", "succubus"], seconds=8.0, extra=["blowjob"], voice=("んっ", "はあ")),
        ov(ride, id="20-straddle-ride", cast=["rei", "succubus"], seconds=8.0, voice=("はあ", "んっ")),
        ov(cream, id="20-straddle-out", cast=["rei", "succubus"], seconds=8.0, voice=("いく", "はあ")),
    ]


def pose_supine() -> list[dict]:
    insert = (
        f"{POSE_BAN}. side view, succubus on her back on the springy meat floor, knees open, wings "
        "spread under her, Rei kneels between her legs, places the 24cm head at the hairless slit then "
        "pushes until the entire shaft is buried to the base and STOPS, insertion locked, no thrusting "
        "yet, claws on Rei's shoulders"
    )
    piston = (
        f"{POSE_BAN}. same bodies same side-view angle as the previous clip, only after the hilt is "
        "already buried do the hips start an in-and-out: pull out to mid-shaft then slam back to the "
        "base, repeat, then creampie overflow, Rei orgasm face tongue out drool runny nose trembling, "
        "succubus climax face, 24cm stays buried then stays erect after pullout"
    )
    return [
        ov(insert, id="20-supine-in", cast=["rei", "succubus"], seconds=8.0, voice=("はあ", "んっ")),
        ov(piston, id="20-supine-out", cast=["rei", "succubus"], seconds=8.0, voice=("いく", "はあ")),
    ]


def build() -> dict:
    s05 = (
        "Only Rei and this one beast. 16:9 side view. The beast stays on all fours in a lizard crawl, "
        "body twice Rei's height. From the right, the circular orange-red oral disc turns toward Rei's "
        "groin. The ring of white triangular teeth flares OPEN like a camera iris so the teeth do not "
        "clamp or bite the shaft. The wet inner red funnel slides FORWARD over the 24cm penis in one "
        "continuous swallow until the circular fleshy rim SEALS at the base. The entire shaft disappears "
        "inside the red tunnel. Outer mint-gray snout flesh bunches. Purple lightning veins pulse. Thick "
        "slime hangs from the lower rim. Then continue without a cut: the circular lip-ring STAYS LOCKED "
        "at the base. Motion is NOT a human head bob and NOT a human jaw chew. The orange-red inner wall "
        "performs PERISTALSIS: concentric rings of flesh contract and travel from the sealed lip toward "
        "the deep gullet, then reverse, milking the shaft root-to-tip-to-root. Travel distance of the inner "
        "rings along the shaft is about 8 to 12cm while the outer rim does not break the seal. The tooth-ring "
        "twitches but stays flared open. The throat visibly gulps slime. At second 5 Rei climaxes: tongue out, "
        "drool running from the mouth corner, runny nose, trembling. Thick ejaculation pumps into the gullet. "
        "Overflow drips from the tooth ring. The inner rings clamp once on the last pulse and hold. Do not "
        "shrink the beast to human size. Do not grow a human face. Keep the tooth-ring visible and flared"
    )
    moth_tail = (
        "Only Rei and this one moth-girl. Meat walls only. The orifice at the TIP of the moth tail is a "
        "SECOND MOUTH, not a human vulva and not located between human thighs. The segmented insect abdomen "
        "curls, the tail hooks under toward Rei's groin. The wet circular opening at the tail tip flares, "
        "then slides onto the 24cm shaft until the tail-mouth SEALS at the base. Inner tail-throat performs "
        "PERISTALSIS: rings of insect flesh contract root-to-tip along the buried shaft. The moth-girl's "
        "human upper body holds Rei from the front or side. Wings spread. Extra insect legs brace on the meat "
        "floor. No human pelvis appears. Then Rei climax: tongue out, drool, runny nose, trembling, thick "
        "ejaculation pumping into the tail-throat, overflow at the sealed tail-rim. 24cm stays erect after"
    )
    moth_mouth = (
        "Only Rei and this one moth-girl. Meat walls only. Shot 1: moth-girl's HUMAN upper face leans in. "
        "Her human tongue enters Rei's mouth. Antennae and moth wings stay in frame. Insect abdomen and extra "
        "legs remain visible behind her. She does not grow human thighs. Shot 2: her human lips part and slide "
        "down the 24cm shaft until they reach the base. Her tongue presses the underside and travels base-to-head "
        "on each return. Her head moves along the shaft. Saliva strings. Human upper limbs may hold Rei's hips. "
        "The moth tail hangs unused. Then Rei orgasm face: tongue out, drool, runny nose"
    )
    beats = [
        beat(
            "01-open-stroke",
            "side view 16:9, Rei standing in the living meat-wall cave, not running, knees slightly bent, "
            "both hands sliding along her fully erect 24cm penis from base to head repeatedly, grip traveling "
            "the full 24cm, ecstatic flushed face, springy flesh floor not sinking, wet pulsating walls. "
            "Do not ejaculate in this clip. Cut just before she starts running right",
            seconds=8.0,
            voice=("はあ", "んっ"),
            stage="01",
        ),
        beat(
            "02-run-a",
            "side-scrolling runner shot, Rei sprinting left to right through the viscera corridor, long brown "
            "hair flowing, erect 24cm penis bouncing with each stride, torn damp thin garment half-off, meat "
            "walls scrolling, no enemy in frame",
            seconds=6.0,
            voice=("はあ",),
            stage="01",
        ),
        mast_pair("03", "01"),
        beat(
            "04-enemy1",
            "side view 16:9 encounter, Rei on the left facing right, giant aberrant beast twice Rei's height "
            "crawling in from the right on four limb-fins, circular orange-red toothed maw opening like an iris, "
            "slime drooling, NO human face, NO human hands, NO human lips, NO human jaw, brief pause, only Rei "
            "plus this one beast",
            cast=["rei", "beast"],
            seconds=6.0,
            extra=["mystic"],
            voice=("はあ",),
            stage="01",
            cut=True,
        ),
        beat(
            "05-enemy1-maw",
            s05,
            cast=["rei", "beast"],
            seconds=10.0,
            extra=["mystic"],
            voice=("んっ", "いく"),
            stage="01",
        ),
        beat(
            "06-fade-run-b",
            "The giant circular-maw beast completely fades out of frame, no walk-away, no residual fin or tooth. "
            "Rei alone in the meat corridor, still fully erect 24cm after ejaculation, then she sprints left to "
            "right, penis bouncing, torn damp garment half-off, no extra people",
            seconds=6.0,
            voice=("はあ",),
            stage="01",
            cut=True,
        ),
        mast_pair("07", "01"),
        beat(
            "08-toilet",
            "side view 16:9, Rei on the left facing a western-toilet shape grown from the meat wall, the bowl "
            "and seat made of packed sticky dark-brown viscous feces not ceramic, living shit-sculpture toilet, "
            "no other people, brief pause",
            seconds=6.0,
            voice=("んっ",),
            stage="02",
            cut=True,
        ),
        beat(
            "09-toilet-act",
            "side view, Rei sitting on a western-shaped toilet sculpted from packed feces inside meat walls, "
            "not ceramic, both hands sliding the 24cm penis base-to-head until thick ejaculation arcs, sticky "
            "dark-brown shit clinging to buttocks and thighs, ecstatic face, tongue starting to slack, only Rei "
            "in frame, then the toilet scene completely fades",
            seconds=8.0,
            voice=("いく", "はあ"),
            slot="toilet",
            stage="02",
            overlays={
                "rei_toilet_ta": ov(
                    "side view, Rei sitting on a western-shaped toilet sculpted from packed feces inside meat "
                    "walls, not ceramic, both hands sliding the 24cm penis base-to-head until thick ejaculation "
                    "arcs, sticky dark-brown shit clinging to buttocks and thighs, ecstatic face, tongue starting "
                    "to slack, only Rei in frame, then the toilet scene completely fades",
                    id="09-ta",
                    seconds=8.0,
                    voice=("いく", "はあ"),
                ),
                "rei_toilet_tb": ov(
                    "side view, same packed-feces western-shaped toilet, not ceramic, Rei seated, a visible urine "
                    "stream leaving the erect 24cm penis into the filthy bowl, brown viscous feces smearing her "
                    "ass and thighs, only Rei in frame, then the toilet scene completely fades",
                    id="09-tb",
                    seconds=8.0,
                    voice=("んっ", "はあ"),
                ),
                "rei_toilet_tc": ov(
                    "side view, Rei scooping packed feces from the living toilet with both hands and spreading it "
                    "over face, breasts, belly, penis and legs until the whole body is coated in thick dark-brown "
                    "shit, stronger filth, only Rei in frame, then the toilet scene completely fades",
                    id="09-tc",
                    seconds=8.0,
                    voice=("んっ", "はあ"),
                ),
            },
        ),
        beat(
            "10-run-c",
            "side-scrolling runner shot, Rei sprinting left to right through viscera corridor, long brown hair "
            "flowing, erect 24cm penis bouncing, torn damp thin garment half-off, meat walls scrolling, no enemy "
            "in frame",
            seconds=6.0,
            voice=("はあ",),
            stage="02",
            cut=True,
        ),
        mast_pair("11", "02", filthy=True),
        beat(
            "12-moth",
            "side view encounter, moth-girl emerging from the meat wall on the right, same height as Rei, "
            "attractive flushed human female face, brown hair, curled ram-like insect antennae, nude beautiful "
            "human female torso, lower body stays insect: segmented moth abdomen, many thin insect legs, cream "
            "moth wings with purple-gray eyespots, tapering stinger-like tail with a wet circular orifice at the "
            "tip, Meat-wall corridor only, only Rei plus this one moth-girl, brief pause",
            cast=["rei", "moth"],
            seconds=6.0,
            extra=["mystic"],
            voice=("はあ",),
            stage="03",
            cut=True,
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
            overlays={
                "rei_moth_tail": ov(moth_tail, id="13-tail", extra=["mystic"], seconds=10.0, voice=("んっ", "いく"), cast=["rei", "moth"]),
                "rei_moth_mouth": ov(moth_mouth, id="13-mouth", extra=["blowjob"], seconds=10.0, voice=("んっ", "いく"), cast=["rei", "moth"]),
            },
        ),
        beat(
            "14-fade-run-d",
            "The moth-girl completely fades out of frame, no walk-away, no residual wing, antenna, or tail. "
            "Rei alone, still fully erect 24cm, then she sprints left to right through the meat corridor, "
            "penis bouncing, no extra people",
            seconds=6.0,
            voice=("はあ",),
            stage="03",
            cut=True,
        ),
        mast_pair("15", "03", filthy=True),
        beat(
            "16-succ",
            "side view 16:9, succubus dropping in from the right of the meat corridor, fully nude bare skin, "
            "hairless vulva, exposed breasts and slit, wings remain, horns remain, choker remains, face marks "
            "remain, hand claws remain, foot claws remain, obsessed expression, reaching for Rei, only Rei plus "
            "this one succubus, brief pause",
            cast=["rei", "succubus"],
            seconds=6.0,
            voice=("はあ",),
            stage="04",
            cut=True,
        ),
        beat(
            "17-attack",
            "side view, Rei grabs the succubus by the waist and presses her to the meat wall, dominant, 24cm "
            "erect against the succubus belly, wings pinned back, claws visible, fully nude succubus, only these two",
            cast=["rei", "succubus"],
            seconds=6.0,
            voice=("んっ", "はあ"),
            slot="attack",
            stage="04",
            overlays={
                "rei_attack_rei": ov(
                    "side view, Rei grabs the succubus by the waist and presses her to the meat wall, dominant, "
                    "24cm erect against the succubus belly, wings pinned back, claws visible, fully nude succubus, "
                    "only these two",
                    id="17-from-rei",
                    cast=["rei", "succubus"],
                ),
                "rei_attack_her": ov(
                    "side view, succubus pounces, torn pink-red wings wrap Rei, tongue on Rei's neck, claws on "
                    "Rei's hips, 24cm trapped between their bellies, fully nude, only these two",
                    id="17-from-her",
                    cast=["rei", "succubus"],
                ),
            },
        ),
        beat(
            "18-kiss",
            "side view, both tongues visible inside an open-mouth kiss, saliva string, succubus red eyes "
            "half-lidded, horns and choker in frame, torn wings behind, fully nude, only these two",
            cast=["rei", "succubus"],
            seconds=6.0,
            voice=("んっ",),
            slot="kiss",
            stage="04",
            overlays={
                "rei_kiss_on": ov(
                    "side view, both tongues visible inside an open-mouth kiss, saliva string, succubus red eyes "
                    "half-lidded, horns and choker in frame, torn wings behind, fully nude, only these two",
                    id="18-kiss-on",
                    cast=["rei", "succubus"],
                ),
            },
        ),
        beat(
            "19-oral",
            "succubus kneels in side view. Her lips part over the head of the 24cm penis, slide to the base, "
            "hold, then pull back to the head. Repeat. Tongue flat on the underside. Spit strings from her lower "
            "lip. Red eyes look along the shaft. Wings folded. Horns, choker, hand claws stay. Fully nude, hairless. "
            "Do not cut the clip before several full base-to-head passes. Only these two",
            cast=["rei", "succubus"],
            seconds=8.0,
            extra=["blowjob"],
            voice=("んっ", "はあ"),
            slot="oral",
            stage="04",
            overlays={
                "rei_oral_her": ov(
                    "succubus kneels in side view. Her lips part over the head of the 24cm penis, slide to the "
                    "base, hold, then pull back to the head. Repeat. Tongue flat on the underside. Spit strings from "
                    "her lower lip. Red eyes look along the shaft. Wings folded. Horns, choker, hand claws stay. "
                    "Fully nude, hairless. Do not cut the clip before several full base-to-head passes. Only these two",
                    id="19-oral-her",
                    extra=["blowjob"],
                    seconds=8.0,
                    voice=("んっ", "はあ"),
                    cast=["rei", "succubus"],
                ),
                "rei_oral_rei": ov(
                    "Rei kneels or bends. Tongue travels up the succubus hairless slit from bottom to top, then "
                    "circles the clitoris. Succubus stands or sits on the meat floor, wings open, thighs apart, mouth "
                    "falling open, horns and claws in frame, fully nude. Only these two",
                    id="19-oral-rei",
                    extra=[],
                    seconds=8.0,
                    voice=("んっ", "はあ"),
                    cast=["rei", "succubus"],
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
            overlays={
                "rei_pose_fours": pose_fours(),
                "rei_pose_wall": pose_wall(),
                "rei_pose_straddle": pose_straddle(),
                "rei_pose_supine": pose_supine(),
            },
        ),
        beat(
            "21-orgasm",
            "side view, Rei orgasm face, tongue out, drool, runny nose, trembling, visible creampie overflow "
            "around the 24cm where it is still buried, succubus climax face, 24cm stays buried then stays erect "
            "after pullout, wings horns choker claws still on the nude succubus, no extra people",
            cast=["rei", "succubus"],
            seconds=8.0,
            voice=("いく", "はあ"),
            stage="04",
        ),
        beat(
            "22-succ-fade",
            "succubus fades completely out of frame, no walk-away, no residual wing or tail or horn, Rei alone, "
            "still erect 24cm, then she starts running right through the meat corridor",
            seconds=6.0,
            voice=("はあ",),
            stage="04",
            cut=True,
        ),
        beat(
            "23-run-e",
            "side-scrolling runner shot, Rei sprinting left to right toward a bright tear of light at the RIGHT "
            "end of the meat corridor, erect 24cm bouncing, torn damp garment half-off, no enemy",
            seconds=6.0,
            voice=("はあ",),
            stage="04",
        ),
        beat(
            "24-escape",
            "side-scrolling exit, a bright tear of light at the right end of the meat corridor, Rei running into "
            "the light, leaving the living cave, the aphrodisiac haze breaking, she still has the 24cm erect penis, "
            "she does not wash, Outside may stop on dark rock. Do not erase the penis",
            seconds=6.0,
            voice=("はあ",),
            stage="EXIT",
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
            "rei_moth": "tail",
            "rei_attack": "rei",
            "rei_kiss": "off",
            "rei_oral": "skip",
            "rei_pose": "fours",
        },
        "style": (
            "Third-person side-scrolling game cutscene look, live-action photoreal game footage, "
            "pulled-back full-body PROFILE framing, brisk real-time playback, no anime, no illustration"
        ),
        "violence": "none",
        "world": {
            "name": "Living meat-wall interior",
            "lock": WORLD,
            "no_text_on_signs": True,
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
                "name_ja": "蛾女",
                "name_en": "Moth",
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
