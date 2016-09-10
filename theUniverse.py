#! /usr/bin/env python

##########################################################
# Stuff to make Pyinstaller work
'''import packaging
import packaging.version
import packaging.specifiers
import packaging.requirements
import appdirs'''

##########################################################
# Imports that are accutally used in this program
import pygame
pygame.init() # probably not needed
import pygame.freetype 
pygame.freetype.init() # makes font work

from operator import sub
from math import sinh, cosh, tanh, copysign

##########################################################
# Defining grapichs options

screenSize = 600, 600

universeSize = 600, 500
universePos = 0, 0

controlesSize = 600, 500
controlesPos = 0, 500

yellow = 240, 222, 5
darkYellow = 50, 50, 0
green = 0, 255, 0
red = 255, 0, 0
blue = 0, 0, 225
gray = 100, 100, 100
darkGray = 50, 50, 50
lightGray = 150, 150, 150
white = 255, 255, 255
black = 0, 0, 0

controlsBgColor = gray 
buttonColor = lightGray
activeButtonColor = darkGray
textColor = black

universeColor = black # universe background color
lightconeColor = darkYellow
lightlikeColor = yellow
spacelikeColor = red
timelikeColor = green
dotColor = blue

lineWidth = 5
dotRadius = 5
lightconeLineWidth = lineWidth

screen = pygame.display.set_mode(screenSize)

##############################################################
# Defining math and such

class Universe:
    
    def get_origo(self):
        return self.surface.get_rect().center 
        # objects in the universe will use coorinates centered at origo
                
    def draw_lightcone(self):
        x, y = self.get_origo()
        dist = min(x, y) # distance to cloest edge

        pygame.draw.line(self.surface,lightconeColor, 
                         (x-dist, y-dist), (x+dist, y+dist),
                         lightconeLineWidth)
                         
        pygame.draw.line(self.surface, lightconeColor, 
                         (x+dist, y-dist), (x-dist, y+dist),
                         lightconeLineWidth)
                               
    def clear(self): # empty the Universe
        self.frame = 0 # lorents frame represented by a number     
        self.lines = [] # objets in the universe
        self.dots = []  # objets in the universe
        
    def __init__(self, size):
        self.surface = pygame.Surface(size) # Here be Universe
        self.clear() # start empty
        
    def draw_in_frame(self, frame):
        ''' draws the universe and all objects in it, 
        in the specified lorents frame '''
        self.surface.fill(universeColor)
        self.draw_lightcone()
            
        for line in self.lines:
            coords = line.in_other_frame(frame)
                # convert to specified lorentz frame
            pos = tuple(spacetime_to_pixel(self, coord) 
                        for coord in coords)
                # converts to pixle possition
            pygame.draw.line(self.surface, line.color(), pos[0], pos[1], lineWidth)
                    
        for dot in self.dots:
            coord = dot.in_other_frame(frame)           
            pos = spacetime_to_pixel(self, coord)
            pygame.draw.circle(self.surface, dotColor, pos, dotRadius)

        
    def draw(self):
        # draws the unierse and all objets in int
        self.draw_in_frame(self.frame)
        
        
def lorentz_transform(coord, frame_diff): 
    sh, ch = sinh(frame_diff), cosh(frame_diff)
    t, r = coord  
    return (ch*t - sh*r, 
           -sh*t + ch*r)
    
def pixel_to_spacetime(universe, pos):
    # takes pixle position and gives space-time coordinates 
    origo = universe.get_origo()
    t = -(pos[0] - origo[0]) # time coordinate
    r = pos[1] - origo[1] # space coordinate
    return t, r
    
def spacetime_to_pixel(universe, coord):
    origo = universe.get_origo()
    x = int(round(origo[0] - coord[0]))
    y = int(round(origo[1] + coord[1]))
    return x, y

class Dot:
    def __init__(self, frame, coord):
        self.coord = coord # space-time coordinate
        self.frame = frame 
            # the lorentz frame in which the object is defined
        
    def in_other_frame(self, display_frame):
        return lorentz_transform(self.coord, display_frame - self.frame)
        # gives space-time coordinates in display_frame
        
        
def make_dot(universe, pos):
    # takes the pixel possition of a point, and makes a Dot object  
    dot = Dot(universe.frame, 
              pixel_to_spacetime(universe, pos) )
    universe.dots.append(dot) # adds objet to universe content
    return dot  
    
def line_color(coords):
    '''diffrent colors to show if the line is 
    time-like, light-like or space like'''
    time  = abs( coords[1][1] - coords[0][1] )
    space = abs( coords[1][0] - coords[0][0] )
    if time > space: 
        return timelikeColor
    elif time == space: 
        return lightlikeColor
    else:
        return spacelikeColor 

    
class Line:
    def __init__(self, frame, coords):
        self.frame = frame
        self.coords = coords # end point coordinates
        
    def in_other_frame(self, display_frame):
        return tuple(lorentz_transform(coord, display_frame - self.frame)
                     for coord in self.coords )
    
    def color(self):
        return line_color(self.coords)

            
def make_line(universe, pos):
    # takes a tuple of two pixle possitions and makes a Line object
    coords = tuple(pixel_to_spacetime(universe, point) 
                   for point in pos) # convert to spacetime coordinates
    line = Line(universe.frame, coords)
    universe.lines.append(line) # adds objet to list
    return line
        
        
###################################################################
# Creating the GUI


clock = pygame.time.Clock() # clock to have clock-ticks, to save on CPU

running = True # Is program running? Assign "False" to quit.
is_drawing_line = False # Is the user in the middle of drawin a line?
shift_is_down = False # the shift key is down

universe = Universe(universeSize) # create empty universe
controls = pygame.Rect(controlesPos, controlesSize) # define control area

#font = pygame.freetype.Font('/home/tilia/anaconda3/lib/python3.5/site-packages/pygame/freesansbold.ttf', 18) # for Pyinstaller
font = pygame.freetype.Font(None, 18)
 


class Button:
    def __init__(self, pos, size, text):
        self.rect = pygame.Rect(pos, size)
        self.text = font.render(text, textColor)[0]
        self.is_active = False
        self.textpos = self.text.get_rect(center=self.rect.center).topleft
        
    def draw(self): # draws button on screen
        if self.is_active:
            pygame.draw.rect(screen, activeButtonColor, self.rect)
        else:
            pygame.draw.rect(screen, buttonColor, self.rect)
                    
        screen.blit(self.text, self.textpos) # put text on button
    
# Create all buttons    
lineButton   = Button((10, 510), (80, 35), "Lines")
dotButton    = Button((10, 555), (80, 35), "Points")
removeButton = Button((100, 510), (80, 35), "Remove") 
clearButton  = Button((100, 555), (80, 35), "Clear")

buttons = (lineButton, dotButton, removeButton, clearButton) # All buttons

drawingOptions = (lineButton, dotButton, removeButton) 
    # These buttons that can not be acctive simultaniously

class Scrol_bar:
    def __init__(self, pos, size):
        self.rect = pygame.Rect(pos, size)
        self.is_grabed = False
        self.max = int((size[0] - size[1])/2)
        self.handle = pygame.Rect((pos[0] + self.max, pos[1]), (size[1], size[1]))
           
    def draw(self, shift): 
        ''' draws the scrollbar, 
        where the handle is moved from the center 
        by the lenght "shift"'''
        pygame.draw.rect(screen, darkGray, self.rect)
        pygame.draw.rect(screen, lightGray, self.handle.move(shift, 0))
        
class Text_display: # Creates a place to display text
    def __init__(self, pos, size):
        self.rect = pygame.Rect(pos, size)
        
    def display(self, text): # Display specified text
        pygame.draw.rect(screen, controlsBgColor, self.rect)
        text = font.render(text, textColor)[0]
        textpos = text.get_rect(center=self.rect.center).topleft
        screen.blit(text, textpos)
        
    def hide(self): # Erase any text
        pygame.draw.rect(screen, controlsBgColor, self.rect)    
        
        
scrol_bar = Scrol_bar((200, 520), (380, 30)) 
    # one scrol bar to specify lorens transfomrations
text_display = Text_display((200, 560), (380, 30))
    # one text display to show the related velocity change

universe.draw() # draws universe
screen.blit(universe.surface, universePos)

pygame.draw.rect(screen, controlsBgColor, controls) # draws controls bacground

for button in buttons: 
    button.draw() # draws button
    
scrol_bar.draw(0) # draws scrol bare, with the handle in the center.

pygame.display.flip() # make all appear on screen


###################################################################
# Running the program

def remove(universe, pos):
    coord = pixel_to_spacetime(universe, pos)
    for dot in universe.dots:
        dot_coord = dot.in_other_frame(universe.frame)
        dist_sq = (coord[0] - dot_coord[0])**2 + (coord[1] - dot_coord[1])**2
        if dist_sq <= dotRadius**2:
            universe.dots.remove(dot)
            return 1
            
    for line in universe.lines:
        line_coords = line.in_other_frame(universe.frame) 
        if line_coords[1][0] - line_coords[0][0] == 0:
            if (coord[0] - line_coords[0][0] <= lineWidth/2
                and coord[1] <= max(line_coords[0][1], line_coords[1][1])
                and coord[1] >= min(line_coords[0][1], line_coords[1][1])):
                universe.lines.remove(line)
                return 2
        
        elif (coord[0] <= max(line_coords[0][0], line_coords[1][0]) + lineWidth/2
            and coord[0] >= min(line_coords[0][0], line_coords[1][0]) - lineWidth/2
            and abs(coord[1] - (line_coords[0][1] + (coord[0] - line_coords[0][0])*(line_coords[1][1] - line_coords[0][1])/(line_coords[1][0] - line_coords[0][0]))) <= lineWidth/2):
            universe.lines.remove(line)
            return 2
    return 0      
            
def straighten_line(start, end):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if abs(dx) < abs(dy)/2:
        return start[0], end[1]
    elif abs(dy) < abs(dx)/2:
        return end[0], start[1]
    else: 
        dx = copysign(dy,dx)
        return start[0] + dx, end[1]

def in_the_universe(pos):
    return universe.surface.get_rect(topleft=universePos).collidepoint(pos)
        

while running:
    for event in pygame.event.get(): # what the user is dooing
        if event.type == pygame.QUIT:
            running = False # time to stop running program
            break # don't check more events
            
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # a left click
        
            if in_the_universe(event.pos): 
                # a click in universe
                     
                if dotButton.is_active:
                    make_dot(universe, event.pos) # make dot there
                    pygame.draw.circle(screen, dotColor, event.pos, dotRadius)
                        # draw the dot
                    
                elif lineButton.is_active:
                    if is_drawing_line: # already makred start of line
                        end = event.pos
                        if shift_is_down:
                            end = straighten_line(start, end)
                        make_line(universe, (start, end))
                        is_drawing_line = False # line is now done
                    else:
                        start = event.pos # remember start of line
                        is_drawing_line = True # drawing in progress
                        universe.draw() # prepare frechly drwan universe
                        
                elif removeButton.is_active:
                    remove(universe, event.pos) # not finnished!
                    universe.draw()
                    screen.blit(universe.surface, universePos)
                    
            elif scrol_bar.handle.collidepoint(event.pos): # click on scrol bar handle
                scrol_bar.is_grabed = True
                grab_pos = event.pos[0] # save x-pos of where it was grabed
                shift = 0 # not draged yet
                    
            else: # click some where else
                for button in buttons: # loop all buttons
                    if button.rect.collidepoint(event.pos): 
                            # chek if we are on this button
                        button.is_active = not button.is_active # change is active
                        button.draw() # re-draw button
                        
                        if button in drawingOptions:
                            for other_button in drawingOptions:
                                if other_button != button:
                                    other_button.is_active = False
                                    other_button.draw() 
                            # can't have more than one of this accitve at the same time
                        
                        if is_drawing_line:
                            is_drawing_line = False # interups any half finiched line
                            screen.blit(universe.surface, universePos) # paint over half finiched line
                            
                        break # no need to check other buttons
                        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # a right click
        
            if is_drawing_line: # interups any half finiche line
                is_drawing_line = False 
                screen.blit(universe.surface, universePos) # paint over half finiched line
            
            if scrol_bar.is_grabed: # interupts any lorentz transformation
                scrol_bar.is_grabed = False 
                scrol_bar.draw(0)
                universe.draw()
                screen.blit(universe.surface, universePos) # paint over half finiched line
                text_display.hide()
                               
        elif event.type == pygame.MOUSEBUTTONUP:
            if clearButton.is_active:
                universe.clear() # celar universe
                universe.draw() # re-draw universe
                screen.blit(universe.surface, universePos) # paint over half finiched line
                clearButton.is_active = False # reset button
                clearButton.draw() # re-draw button
            
            elif scrol_bar.is_grabed: # finalizes any lorentz transformation
                scrol_bar.is_grabed = False
                scrol_bar.draw(0)
                universe.frame += 0.01 * shift
                text_display.hide()
                    
        elif event.type == pygame.MOUSEMOTION:
            if is_drawing_line: 
                if in_the_universe(event.pos):
                    end = event.pos
                    if shift_is_down:
                        old_end = end
                        end = straighten_line(start, end)
                    screen.blit(universe.surface, universePos) 
                    color = line_color((start, end))
                    pygame.draw.line(screen, color, start, end, lineWidth)
                else:
                    last_pos = tuple(map(sub, event.pos, event.rel))
                    if in_the_universe(last_pos):
                        screen.blit(universe.surface, universePos)
                        
            elif scrol_bar.is_grabed:
                shift = event.pos[0] - grab_pos
                if shift < -scrol_bar.max:
                    shift = -scrol_bar.max
                elif shift > scrol_bar.max:
                    shift = scrol_bar.max    
                
                universe.draw_in_frame(universe.frame + 0.01 * shift)
                screen.blit(universe.surface, universePos)      
                    
                scrol_bar.draw(shift)
                text_display.display("Instantly accelerate to "
                                     + str(round(100 * tanh(0.01 * shift)))
                                     + "% of light speed.")
                                     
        elif event.type == pygame.KEYDOWN and (event.key == pygame.K_LSHIFT
                                            or event.key == pygame.K_RSHIFT):
            shift_is_down = True
            if is_drawing_line:
                end = straighten_line(start, end)
                screen.blit(universe.surface, universePos)
                color = line_color((start, end))
                pygame.draw.line(screen, color, start, end, lineWidth)
                
        elif event.type == pygame.KEYUP and (event.key == pygame.K_LSHIFT
                                            or event.key == pygame.K_RSHIFT):
            shift_is_down = False
            if is_drawing_line:
                end = old_end
                screen.blit(universe.surface, universePos)
                color = line_color((start, end))
                pygame.draw.line(screen, color, start, end, lineWidth)
                    

        pygame.display.flip() # show changes    
        
    clock.tick(120) # to save on CPU use


 



    
