from __future__ import division

import os
import sys, time, random, pygame

from scipy.spatial import distance as dist
from imutils.video import VideoStream, FPS
from imutils import face_utils
import imutils
import numpy as np
import time
import dlib


from collections import deque
import cv2 as cv

FONTS =cv.FONT_HERSHEY_COMPLEX
PREVIEW_TEXT_COLOUR = (0, 255, 255)

pygame.init()
clock = pygame.time.Clock()

MAR_THRESHOLD = 1.0
MAR_CONSECUTIVE_FRAMES = 3
JUMP_HEIGHT = 5
JUMP_GRAVITY = 12
GRAVITY = 50
JUMP_SPEED = 10
jump = 0


def smile(mouth):
    A = dist.euclidean(mouth[3], mouth[9])
    B = dist.euclidean(mouth[2], mouth[10])
    C = dist.euclidean(mouth[4], mouth[8])
    avg = (A+B+C)/3
    D = dist.euclidean(mouth[0], mouth[6])
    mar = avg/D
    return mar

def check_collision(pipe_frames):
    if any([bird_frame.colliderect(pf[0]) or bird_frame.colliderect(pf[1]) for pf in pipe_frames]):
        return False
    if bird_frame.top <= 100 or bird_frame.bottom >= 900:
        return False
    return True



shape_predictor= 'shape_predictor_68_face_landmarks.dat'
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(shape_predictor)
(mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]


# Initialize required elements/environment
VID_CAP = cv.VideoCapture(0)
window_size = (VID_CAP.get(cv.CAP_PROP_FRAME_WIDTH), VID_CAP.get(cv.CAP_PROP_FRAME_HEIGHT))  # width by height
screen = pygame.display.set_mode(window_size)
VID_CAP.set(cv.CAP_PROP_POS_FRAMES, 10)
fps = int(VID_CAP.get(5))
print("fps:", fps)

# Bird and pipe init
bird_img = pygame.image.load("bird_sprite.png").convert_alpha()
bird_img = pygame.transform.scale(bird_img, (bird_img.get_width() / 9, bird_img.get_height() / 9))
bird_frame = bird_img.get_rect()
bird_frame.center = (window_size[0] // 8, window_size[1] // 2)

pipe_frames = deque()
pipe_img = pygame.image.load("pipe_sprite_single.png")


pipe_starting_template = pipe_img.get_rect()
space_between_pipes = 250

# Game loop
game_clock = time.time()
stage = 1
pipeSpawnTimer = 0
time_between_pipe_spawn = 50
dist_between_pipes = 500
pipe_velocity = lambda: dist_between_pipes / time_between_pipe_spawn
level = 0
score = 0
high_score = 0
didUpdateScore = False
game_is_running = True


while True:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            VID_CAP.release()
            cv.destroyAllWindows()
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and game_is_running == False:
                bird_frame.center = (window_size[0] // 8, window_size[1] // 2)
                game_is_running = True
                screen.blit(pipe_img, pf[1])
                screen.blit(pygame.transform.flip(pipe_img, 0, 1), pf[0])
                pipe_frames.popleft()
                pipe_frames.popleft()
                time_between_pipe_spawn = 50

    # Check if game is running

    if game_is_running:

        jumpSpeed = JUMP_SPEED
        gravity = JUMP_GRAVITY
        if jump:
            jumpSpeed -= 1
            bird_frame.centery -= jumpSpeed
            jump -= 1
        else:
            bird_frame.centery += gravity
            gravity += 0.2
        
        screen.blit(bird_img, bird_frame)
        # check collision
        game_is_running = check_collision(pipe_frames)

        # Time to add new pipes
        if pipeSpawnTimer == 0:
            top = pipe_starting_template.copy()
            # Check that the range is not empty before calling randint()
            if window_size[1] - 120 - space_between_pipes - 1000 > 120 - 1000:
                top.x, top.y = window_size[0], random.randint(120 - 1000, window_size[1] - 120 - space_between_pipes - 1000)
            else:   
                # Handle the case where the range is empty
                top.x, top.y = window_size[0], random.randint(0, window_size[1] - 120 - space_between_pipes)           
                #top.x, top.y = window_size[0], random.randint(120 - 1000, window_size[1] - 120 - space_between_pipes - 1000)
            bottom = pipe_starting_template.copy()
            bottom.x, bottom.y = window_size[0], top.y + 1000 + space_between_pipes
            pipe_frames.append([top, bottom])

        pipeSpawnTimer += 1
        if pipeSpawnTimer >= time_between_pipe_spawn:
            pipeSpawnTimer = 0

        # Update pipe positions
        for pf in pipe_frames:
            pf[0].x -= pipe_velocity()
            pf[1].x -= pipe_velocity()

        if len(pipe_frames) > 0 and pipe_frames[0][0].right < 0:
            pipe_frames.popleft()

        # Update screen
        checker = True
        for pf in pipe_frames:
            if pf[0].left <= bird_frame.x <= pf[0].right:
                checker = False
                if not didUpdateScore:
                    score += 1
                    if score > high_score:
                        high_score = score
                    didUpdateScore = True
            # Update screen
            screen.blit(pipe_img, pf[1])
            screen.blit(pygame.transform.flip(pipe_img, 0, 1), pf[0])
        if checker: didUpdateScore = False

        # Update stage
        if time.time() - game_clock >= 4:
            time_between_pipe_spawn *= 5 / 6
            if time.time() - game_clock >= 5:
                stage += 1
            game_clock = time.time()

    else:
        message = pygame.image.load("message.png").convert_alpha()
        game_over_rect = message.get_rect()
        game_over_rect.center = (window_size[0] / 2, window_size[1] / 2)
        screen.blit(message, game_over_rect)
        #screen.fill((125, 220, 232))
        #clock.tick(1000)
        pygame.display.update()
        level = 0
        score = 0
        stage = 1
        didUpdateScore = True
        #game_is_running = True
        pygame.display.flip()
        game_clock = time.time()
        #screen.blit(pipe_img, pf[1])
        #screen.blit(pygame.transform.flip(pipe_img, 0, 1), pf[0])
        # Update pipe positions
        if len(pipe_frames) > 0 and pipe_frames[0][0].right < 0:
            pipe_frames.popleft()
            pipe_frames.popleft()

    pygame.display.update()
    

    # Get frame
    ret, frame = VID_CAP.read()
    if not ret:
        print("Empty frame, continuing...")
        continue

    # Clear screen
    screen.fill((125, 220, 232))
    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    # mouth
    rects = detector(frame, 0)
    for rect in rects:
        shape = predictor(frame, rect)
        shape = face_utils.shape_to_np(shape)
        mouth = shape[mStart:mEnd]
        mar = smile(mouth)
        cv.putText(frame, "MAR: {:.2f}".format(mar), (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        mouthHull = cv.convexHull(mouth)
        cv.drawContours(frame, [mouthHull], -1, (0, 255, 0), 1)

        if mar >= 0.4:
            jump = JUMP_HEIGHT
            gravity = JUMP_GRAVITY
            jumpSpeed = JUMP_SPEED
            #clock.tick(60)
        else:
            gravity = GRAVITY



    # Mirror frame, swap axes because opencv != pygame
    frame = cv.flip(frame, 1).swapaxes(0, 1)
    pygame.surfarray.blit_array(screen, frame)


    # Stage, score text
    text = pygame.font.SysFont("Helvetica Bold.ttf", 50).render(f'Stage {stage}', True, (99, 245, 255))
    tr = text.get_rect()
    tr.center = (100, 50)
    screen.blit(text, tr)
    text = pygame.font.SysFont("Helvetica Bold.ttf", 50).render(f'Score: {score}', True, (99, 245, 255))
    tr = text.get_rect()
    tr.center = (100, 100)
    screen.blit(text, tr)
    text = pygame.font.SysFont("Helvetica Bold.ttf", 50).render(f'High Score: {high_score}', True, (99, 245, 255))
    tr = text.get_rect()
    tr.center = (100, 130)
    screen.blit(text, tr)

    # Update screen
    #pygame.display.flip()


