from analyzer import detect_face_anchor


def build_zoom_keyframes(
    video_path: str,
    transitions: list[float],
    clip_duration: float,
    zoom_scale: float = 1.22,
    mode: str = "punch",
    face_tracking: bool = True,
    ramp_duration: float = 0.35
) -> list[dict]:
    """Gera a lista cronológica de keyframes de escala e ponto de ancoragem."""
    keyframes = []
    zoomed_in = False

    for idx, t in enumerate(transitions):
        if t >= clip_duration:
            break

        if idx > 0:
            zoomed_in = not zoomed_in

        target_scale = zoom_scale if zoomed_in else 1.0
        if zoomed_in and face_tracking:
            anchor_x, anchor_y = detect_face_anchor(video_path, t + 0.1)
        else:
            anchor_x, anchor_y = 0.5, 0.5

        if mode == "punch" or idx == 0:
            if idx > 0 and t - 0.001 > keyframes[-1]["time"]:
                prev = keyframes[-1]
                keyframes.append({
                    "time": round(t - 0.001, 3),
                    "scale": prev["scale"],
                    "anchor_x": prev["anchor_x"],
                    "anchor_y": prev["anchor_y"],
                    "easing": "hold"
                })

            keyframes.append({
                "time": t,
                "scale": target_scale,
                "anchor_x": anchor_x,
                "anchor_y": anchor_y,
                "easing": "hold"
            })
        else:
            ramp_start = max(0.0, round(t - ramp_duration, 3))
            if ramp_start > keyframes[-1]["time"]:
                prev = keyframes[-1]
                keyframes.append({
                    "time": ramp_start,
                    "scale": prev["scale"],
                    "anchor_x": prev["anchor_x"],
                    "anchor_y": prev["anchor_y"],
                    "easing": "ease_in_out"
                })

            keyframes.append({
                "time": t,
                "scale": target_scale,
                "anchor_x": anchor_x,
                "anchor_y": anchor_y,
                "easing": "ease_in_out"
            })

    return keyframes
