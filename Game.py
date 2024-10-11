import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import pywavefront
import cv2
import mediapipe as mp

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 700



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

    def scan_hands(self, image):
        rows, cols, _ = image.shape
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        self.results = self.hand_tracking.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

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
                   
                mp_hands = mp.solutions.hands
                mp_drawing = mp.solutions.drawing_utils
                mp_drawing_styles = mp.solutions.drawing_styles
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

        return image

    def is_hand_closed(self):
        return self.hand_closed

class OpenGLScene:
    
    def __init__(self):
        self.hand_tracker = HandTracking()
        pygame.init()
        display = (800, 600)
        pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
        gluPerspective(45, (display[0] / display[1]), 1, 500.0)
        glTranslatef(0.0, 0.0, -10)

        self.scene = pywavefront.Wavefront('Cube.obj', collect_faces=True)
        self.scene_box = self.calculate_scene_box()
        self.scene_trans = [-(self.scene_box[1][i] + self.scene_box[0][i]) / 2 for i in range(3)]
        self.scene_scale = self.calculate_scene_scale()
        self.angle = 0
        

        
    def calculate_scene_box(self):
        scene_box = (self.scene.vertices[0], self.scene.vertices[0])
        for vertex in self.scene.vertices:
            min_v = [min(scene_box[0][i], vertex[i]) for i in range(3)]
            max_v = [max(scene_box[1][i], vertex[i]) for i in range(3)]
            scene_box = (min_v, max_v)
        return scene_box

    def calculate_scene_scale(self):
        scaled_size = 3
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

    def main_loop(self):
        hand_tracker = HandTracking()
        hand_position_prev_x = 0
        hand_position_prev_y = 0
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()


            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glPushMatrix()
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glPopMatrix()
            glRotatef(1, 5, 1, 1)
            self.draw_model()

            pygame.display.flip()
            pygame.time.wait(15)
            cap = cv2.VideoCapture(0)  
            ret, frame = cap.read()
            processed_frame = hand_tracker.scan_hands(frame)
            hand_closed = hand_tracker.is_hand_closed()
            if hand_closed:
                hand_position_curr_x = hand_tracker.hand_x  
                hand_position_curr_y = hand_tracker.hand_y
                if hand_position_curr_x > hand_position_prev_x:
                    glTranslatef(0.1, 0, 0)
                elif hand_position_curr_x < hand_position_prev_x:
                   glTranslatef(-0.1, 0, 0)  
                if hand_position_curr_y > hand_position_prev_y:
                        glTranslatef(0, 0.1, 0)  
                elif hand_position_curr_y < hand_position_prev_y:
                   glTranslatef(0, -0.1, 0)
                hand_position_prev_x = hand_position_curr_x
                hand_position_prev_y = hand_position_curr_y
                
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 1200

def main():
    scene = OpenGLScene()
    scene.main_loop()

if __name__ == "__main__":
    main()
