import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import pywavefront
import cv2
import mediapipe as mp
import random

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

class HandTracking:
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    
    def __init__(self):
        mp_hands = mp.solutions.hands
        self.hand_tracking = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.hand_x = 0
        self.hand_y = 0
        self.results = None
        self.hand_closed = False

    def scan_hands(self, frame):
        if frame is None:
            return None
        
        rows, cols, _ = frame.shape
        frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        frame.flags.writeable = False
        self.results = self.hand_tracking.process(frame)
        frame.flags.writeable = True
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        self.hand_closed = False

        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                x, y = hand_landmarks.landmark[9].x, hand_landmarks.landmark[9].y
                self.hand_x = int(x * SCREEN_WIDTH)
                self.hand_y = int(y * SCREEN_HEIGHT)

                x1, y1 = hand_landmarks.landmark[12].x, hand_landmarks.landmark[12].y

                if y1 > y:
                    mp_drawing = mp.solutions.drawing_utils
                    self.hand_closed = True

                mp_hands = mp.solutions.hands
                mp_drawing = mp.solutions.drawing_utils
                mp_drawing_styles = mp.solutions.drawing_styles
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

        return frame

    def is_hand_closed(self):
        return self.hand_closed

class Target:
    def __init__(self):
        self.x = random.randint(50, SCREEN_WIDTH - 50)
        self.y = random.randint(50, SCREEN_HEIGHT - 50)
        self.size = 20
        self.hit = False

    def draw(self):
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(self.x - self.size / 2, self.y - self.size / 2)
        glVertex2f(self.x + self.size / 2, self.y - self.size / 2)
        glVertex2f(self.x + self.size / 2, self.y + self.size / 2)
        glVertex2f(self.x - self.size / 2, self.y + self.size / 2)
        glEnd()

class Cube:
    def __init__(self):
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT / 2
        self.size = 50

    def draw(self):
        glColor3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(self.x - self.size / 2, self.y - self.size / 2)
        glVertex2f(self.x + self.size / 2, self.y - self.size / 2)
        glVertex2f(self.x + self.size / 2, self.y + self.size / 2)
        glVertex2f(self.x - self.size / 2, self.y + self.size / 2)
        glEnd()

class OpenGLScene:
    def __init__(self):
        pygame.init()
        display = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.screen = pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
        gluOrtho2D(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0)

        self.scene = pywavefront.Wavefront('Cube.obj', collect_faces=True)
        self.scene_box = self.calculate_scene_box()
        self.scene_trans = [-(self.scene_box[1][i] + self.scene_box[0][i]) / 2 for i in range(3)]
        self.scene_scale = self.calculate_scene_scale()

        self.hand_tracker = HandTracking()
        self.target = Target()
        self.cube = Cube()
        self.score = 0

        # Initialize font
        self.font = pygame.font.Font(None, 36)

    def calculate_scene_box(self):
        scene_box = (self.scene.vertices[0], self.scene.vertices[0])
        for vertex in self.scene.vertices:
            min_v = [min(scene_box[0][i], vertex[i]) for i in range(3)]
            max_v = [max(scene_box[1][i], vertex[i]) for i in range(3)]
            scene_box = (min_v, max_v)
        return scene_box

    def calculate_scene_scale(self):
        scaled_size = 5
        scene_size = [self.scene_box[1][i] - self.scene_box[0][i] for i in range(3)]
        max_scene_size = max(scene_size)
        return [scaled_size / max_scene_size for i in range(3)]

    def draw_model(self):
        glPushMatrix()
        glScalef(*self.scene_scale)
        glTranslatef(*self.scene_trans)

        for mesh in self.scene.mesh_list:
            glBegin(GL_TRIANGLES)
            for face in mesh.faces:
                for vertex_i in face:
                    glVertex3f(*self.scene.vertices[vertex_i])
            glEnd()

        glPopMatrix()

    def draw_score(self):
        text_surface = self.font.render(f'Score: {self.score}', True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(text_surface, text_rect)


    def main_loop(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
    
            processed_frame = self.hand_tracker.scan_hands(frame)
    
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
    
            glClear(GL_COLOR_BUFFER_BIT)
            self.draw_model()
            self.draw_score()  # Draw the score
    
            if processed_frame is not None:
                self.target.draw()
    
                hand_closed = self.hand_tracker.is_hand_closed()
                if hand_closed:
                    hand_position_curr_x = self.hand_tracker.hand_x  # Current hand position
                    hand_position_curr_y = self.hand_tracker.hand_y
    
                    # Check if the hand hits the target
                    if abs(hand_position_curr_x - self.target.x) < self.target.size / 2 and \
                        abs(hand_position_curr_y - self.target.y) < self.target.size / 2:
                        self.score += 1
                        print(f"Score: {self.score}")  # Print the score for debugging
                        # Respawn target at a random location
                        self.target = Target()
    
                    # Move the cube according to hand movement
                    self.cube.x = hand_position_curr_x
                    self.cube.y = hand_position_curr_y
    
                    self.cube.draw()
    
            pygame.display.flip()
    
        cap.release()
        cv2.destroyAllWindows()


                
def main():
    scene = OpenGLScene()
    scene.main_loop()

if __name__ == "__main__":
    main()
