def read_rocket_frames():
    with open("files/rocket_frame_1.txt") as f:
        frame1 = f.read()

    with open("files/rocket_frame_2.txt") as f:
        frame2 = f.read()

    return frame1, frame2


def read_garbage_frames():
    with open('files/trash_small.txt') as f:
        small_garbage_frame = f.read()

    with open('files/trash_large.txt') as f:
        large_garbage_frame = f.read()

    return small_garbage_frame, large_garbage_frame

