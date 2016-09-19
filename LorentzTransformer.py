#! /usr/bin/env python

##########################################################
# Imports that are accutally used in this program
import pygame
pygame.init() # probably not needed
import pygame.freetype 
pygame.freetype.init() # makes font work

bigfont = pygame.freetype.Font(None, 20)
font = pygame.freetype.Font(None, 14)

import tkinter
import tkinter.filedialog
tkinter.Tk().withdraw() # to not have save and load dialog window, hanging around


from operator import sub
from math import sinh, cosh, tanh, copysign, ceil, log10
import re, random
import json, os, sys, subprocess

##########################################################
# Stuff to make Pyinstaller work
'''
import packaging
import packaging.version
import packaging.specifiers
import packaging.requirements
import appdirs

font = pygame.freetype.Font('/home/tilia/anaconda3/lib/python3.5/site-packages/pygame/freesansbold.ttf', 18)
'''   

##########################################################
# Defining grapichs options

screenSize = 600, 600
universePos = 0, 0
controlsHeight = 55
menuPos = 0, 0

def universe_size(screenSize):
    return screenSize[0], screenSize[1] - controlsHeight
    
def controls_pos(screenSize):
    return 0, screenSize[1] - controlsHeight
    
def controls_size(screenSize):
    return screenSize[0], controlsHeight
    
controlsPos = controls_pos(screenSize)


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

menuColor = lightGray
menuActiveColor = gray

universeColor = black # universe background color
lightconeColor = darkYellow
lightlikeColor = yellow
spacelikeColor = red
timelikeColor = green
pointColor = blue

lineWidth = 5
pointRadius = 5
lightconeLineWidth = lineWidth

screen = pygame.display.set_mode(screenSize, pygame.RESIZABLE)

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
        self.points = []  # objets in the universe
        
    def __init__(self, size):
        self.show_lightcone = True # show lightcone as default
        self.surface = pygame.Surface(size) # Here be Universe
        self.clear() # start empty
        
    def draw_in_frame(self, frame):
        ''' draws the universe and all objects in it, 
        in the specified lorents frame '''
        self.surface.fill(universeColor)
        
        if self.show_lightcone:
            self.draw_lightcone()
            
        for line in self.lines:
            coords = line.in_other_frame(frame)
                # convert to specified lorentz frame
            pos = tuple(spacetime_to_pixel(self, coord) 
                        for coord in coords)
                # converts to pixle possition
            pygame.draw.line(self.surface, line.color(), pos[0], pos[1], lineWidth)
                    
        for point in self.points:
            coord = point.in_other_frame(frame)           
            pos = spacetime_to_pixel(self, coord)
            pygame.draw.circle(self.surface, pointColor, pos, pointRadius)

        
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

class Point:
    def __init__(self, frame, coord):
        self.coord = coord # space-time coordinate
        self.frame = frame 
            # the lorentz frame in which the object is defined
        
    def in_other_frame(self, display_frame):
        return lorentz_transform(self.coord, display_frame - self.frame)
        # gives space-time coordinates in display_frame
        
        
def make_point(universe, pos):
    # takes the pixel possition of a point, and makes a point object  
    point = Point(universe.frame, 
              pixel_to_spacetime(universe, pos) )
    universe.points.append(point) # adds objet to universe content
    universe.draw() # uppdate picture of universe
    return point  
    
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
    universe.draw() # uppdate picture of universe
    return line


###################################################################
# Menu: Help, Save and Load

class MenuButton:
    def __init__(self, name, pos):
        text, rect = font.render(name, textColor)
        self.text = text
        self.rect = pygame.Rect(pos, (rect.width + 10, 20))
        self.textpos = self.text.get_rect(center=self.rect.center).topleft
        
    def draw(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, menuActiveColor, self.rect)
        else:
            pygame.draw.rect(screen, menuColor, self.rect)
        screen.blit(self.text, self.textpos)

menu_names = ("Help", "Save", "Load", "Show/Hide lightcone")
menu_dict =  {}
menu_list = [] 

next_pos = menuPos
for name in menu_names:
    menu_button = MenuButton(name, next_pos)
    menu_dict[name] = menu_button
    menu_list.append(menu_button)
    next_pos = menu_button.rect.topright
    
menu_rect = pygame.Rect(menuPos, (next_pos[0] - menuPos[0], 20))

def draw_menu(mouse_pos):
    for menu_button in menu_list:
        menu_button.draw(mouse_pos)
        
def show_message(text): # will showes message on the screen 
    text, rect = bigfont.render(text, textColor)
    rect.center = screen.get_rect().center
    rect.move_ip(random.randint(-15,15), random.randint(-15,15))
    pygame.draw.rect(screen, gray, rect.inflate(30,30))
    pygame.draw.rect(screen, lightGray, rect.inflate(20,20))
    screen.blit(text, rect.topleft)
    
def help(): # Tries to opens the README
    try:
        if sys.platform == 'linux2' or sys.platform == 'linux':
            subprocess.call(["xdg-open", "README.txt"])
        else:
            os.startfile("README.txt")
    except:
        show_message("Sorry, cant help you")

def universe_to_json(universe):
    points = [{'frame': point.frame, 'coord': point.coord} for point in universe.points]
    lines = [{'frame': line.frame, 'coords': line.coords} for line in universe.lines]
    return json.dumps({'frame': universe.frame, 
                       'show_lightcone': universe.show_lightcone,
                       'points': points,
                       'lines': lines})
                       
def json_to_universe(json_string):
    universe_dict = json.loads(json_string)
    universeSize = universe_size(pygame.dsiplay.get_surface().get_rect().size)
    universe = Universe(universeSize)
    
    universe.frame = universe_dict['frame']
    universe.show_lightcone = universe_dict['show_lightcone']
    
    universe.points = [Point(point['frame'], point['coord']) 
                        for point in universe_dict['points']]
                        
    universe.lines = [Lines(line['frame'], line['coords'])
                        for line in universe_dict['lines']]
    return universe
    

def save():
    if not os.path.exists('Saves/'):
        os.mkdir("Saves")
    file = tkinter.filedialog.asksaveasfile(defaultextension=".lor", initialdir = "Saves")
    if file:
        file.write(universe_to_json(universe))
        file.close()
        show_message('You have saved this Universe')
    
        

def load():
    saves = find_saves()
    if saves:
        load_menu = LoadMenu(saves)  
    else:
        show_message('There is nothing to load')
        
        
###################################################################
# Creating the GUI 

class Button:
    def __init__(self, pos, size, text):
        self.rect = pygame.Rect(pos, size)
        self.text = font.render(text, textColor)[0]
        self.is_active = False
        self.textpos = self.text.get_rect(center=self.rect.center).topleft
        
    def draw(self): # draws button on screen
        if self.is_active:
            pygame.draw.rect(controls, activeButtonColor, self.rect)
        else:
            pygame.draw.rect(controls, buttonColor, self.rect)
                    
        controls.blit(self.text, self.textpos) # put text on button
    
# Create all buttons    
lineButton   = Button((5, 5), (60, 20), "Lines")
pointButton    = Button((5, 30), (60, 20), "Points")
removeButton = Button((70, 5), (60, 20), "Remove") 
clearButton  = Button((70, 30), (60, 20), "Clear")

buttons = (lineButton, pointButton, removeButton, clearButton) # All buttons

drawingOptions = (lineButton, pointButton, removeButton) 
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
        pygame.draw.rect(controls, darkGray, self.rect)
        pygame.draw.rect(controls, lightGray, self.handle.move(shift, 0))
        
class Text_display: # Creates a place to display text
    def __init__(self, pos, size):
        self.rect = pygame.Rect(pos, size)
        
    def display(self, text): # Display specified text
        pygame.draw.rect(controls, controlsBgColor, self.rect)
        text = font.render(text, textColor)[0]
        textpos = text.get_rect(center=self.rect.center).topleft
        controls.blit(text, textpos)
        
    def hide(self): # Erase any text
        pygame.draw.rect(controls, controlsBgColor, self.rect)    
        
        
scrol_bar = Scrol_bar((138, 8), (screenSize[0] - 138 - 8, 18)) 
    # one scrol bar to specify lorens transfomrations
text_display = Text_display((138, 8+18), (screenSize[0] - 138 - 8, 55-8-18))
    # one text display to show the related velocity change
    

controls = pygame.Surface(controls_size(screenSize))
controls.fill(controlsBgColor)

for button in buttons: 
    button.draw() # draws button
    
scrol_bar.draw(0) # draws scrol bare, with the handle in the center.

screen.blit(controls, controlsPos)


universe = Universe(universe_size(screenSize)) # create empty 
universe.draw() # draws universe
screen.blit(universe.surface, universePos) # put on screen

pygame.display.flip() # make all appear on screen


###################################################################
# Running the program

clock = pygame.time.Clock() # clock to have clock-ticks, to save on CPU

running = True # Is program running? Assign "False" to quit.
is_drawing_line = False # Is the user in the middle of drawin a line?
shift_is_down = False # the shift key is down
last_pos = (-1, -1) # pos for last MOUSEMOTION event. Put initial outside screen
last_save_or_load = None

def remove(universe, pos):
    coord = pixel_to_spacetime(universe, pos)
    for point in universe.points:
        point_coord = point.in_other_frame(universe.frame)
        dist_sq = (coord[0] - point_coord[0])**2 + (coord[1] - point_coord[1])**2
        if dist_sq <= pointRadius**2:
            universe.points.remove(point)
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
    return (universe.surface.get_rect(topleft=universePos).collidepoint(pos)
            and not menu_rect.collidepoint(pos) )
    
def my_round(frac):
    if abs(frac) < 90:
        return round(frac)
    if abs(frac) < 99:
        return round(frac,1)
    if abs(frac) < 99.9:
        return round(frac,2)#
    return round(frac, 2-ceil(log10(100-abs(frac))))

while running:
    for event in pygame.event.get(): # what the user is dooing
        if event.type == pygame.QUIT:
            #pygame.display.quit() # close window
            running = False # time to stop running program
            break # don't check more events
            
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # a left click
        
            if menu_dict["Help"].rect.collidepoint(event.pos):
                help()
                
            elif menu_dict["Save"].rect.collidepoint(event.pos):
                save()
                
            elif menu_dict["Load"].rect.collidepoint(event.pos):
                load()
                
            elif menu_dict["Show/Hide lightcone"].rect.collidepoint(event.pos):
                universe.show_lightcone = not universe.show_lightcone
                universe.draw()
                screen.blit(universe.surface, universePos)
                draw_menu(event.pos)
        
            elif in_the_universe(event.pos): 
                # a click in universe
                     
                if pointButton.is_active:
                    make_point(universe, event.pos) # make point there
                    pygame.draw.circle(screen, pointColor, event.pos, pointRadius)
                        # draw the point
                    
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
                        
                elif removeButton.is_active:
                    remove(universe, event.pos) # not finnished!
                    universe.draw()
                    screen.blit(universe.surface, universePos)
                    
            elif scrol_bar.handle.move(controlsPos).collidepoint(event.pos): 
                # click on scrol bar handle
                scrol_bar.is_grabed = True
                grab_pos = event.pos[0] # save x-pos of where it was grabed
                shift = 0 # not draged yet
                    
            else: # click some where else
                for button in buttons: # loop all buttons
                    if button.rect.move(controlsPos).collidepoint(event.pos): 
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
                        screen.blit(controls, controlsPos)    
                        break # no need to check other buttons
                        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # a right click
        
            if is_drawing_line: # interups any half finiche line
                is_drawing_line = False 
                screen.blit(universe.surface, universePos) # paint over half finiched line
            
            if scrol_bar.is_grabed: # interupts any lorentz transformation
                scrol_bar.is_grabed = False 
                scrol_bar.draw(0)
                text_display.hide()
                screen.blit(controls, controlsPos)
                
                universe.draw()
                screen.blit(universe.surface, universePos) # paint over half finiched line
                               
        elif event.type == pygame.MOUSEBUTTONUP:
            if clearButton.is_active:
                universe.clear() # celar universe
                universe.draw() # re-draw universe
                
                screen.blit(universe.surface, universePos) # paint over half finiched line
                clearButton.is_active = False # reset button
                clearButton.draw() # re-draw button
                screen.blit(controls, controlsPos)
            
            elif scrol_bar.is_grabed: # finalizes any lorentz transformation
                scrol_bar.is_grabed = False
                scrol_bar.draw(0)
                universe.frame += 0.01 * shift
                text_display.hide()
                screen.blit(controls, controlsPos)
                    
        elif event.type == pygame.MOUSEMOTION: 
        
            if scrol_bar.is_grabed:
                shift = event.pos[0] - grab_pos
                if shift < -scrol_bar.max:
                    shift = -scrol_bar.max
                elif shift > scrol_bar.max:
                    shift = scrol_bar.max    
                
                universe.draw_in_frame(universe.frame + 0.01 * shift)
                screen.blit(universe.surface, universePos)      
                    
                scrol_bar.draw(shift)
                
                
                
                if text_display.rect.width < 130:
                    text_display.display(str(my_round(100 * tanh(0.01 * shift)))
                                         + "% c")
                                             
                elif text_display.rect.width < 290:
                    text_display.display(str(my_round(100 * tanh(0.01 * shift)))
                                         + "% of light speed")
                else:         
                    text_display.display("Instantly accelerate to "
                                         + str(my_round(100 * tanh(0.01 * shift)))
                                         + "% of light speed.")
                screen.blit(controls, controlsPos)                 
            
            elif is_drawing_line:
                if in_the_universe(event.pos):
                    end = event.pos
                    if shift_is_down:
                        end = straighten_line(start, end)
                    screen.blit(universe.surface, universePos) 
                    color = line_color((start, end))
                    pygame.draw.line(screen, color, start, end, lineWidth)
                    
                elif in_the_universe(last_pos):
                    screen.blit(universe.surface, universePos)
                    
            if menu_rect.collidepoint(event.pos):
                draw_menu(event.pos)
                
            elif not is_drawing_line and menu_rect.collidepoint(last_pos):
                screen.blit(universe.surface,universePos)
            
            last_pos = event.pos      

                                     
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
                end = pygame.mouse.get_pos()
                screen.blit(universe.surface, universePos)
                color = line_color((start, end))
                pygame.draw.line(screen, color, start, end, lineWidth)
                
        elif event.type == pygame.VIDEORESIZE: # resize window
            screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

            universe.surface = pygame.Surface(universe_size(event.size))
            universe.draw()
            screen.blit(universe.surface, universePos)          
            
            controlsPos = controls_pos(event.size)
            controls = pygame.Surface(controls_size(event.size))
            controls.fill(controlsBgColor)
            for button in buttons: 
                button.draw() # draws button
                
            scrol_bar = Scrol_bar((138, 8), (event.size[0] - 138 - 8, 18)) 
            text_display = Text_display((138, 8+18), (event.size[0] - 138 - 8, 55-8-18))
            scrol_bar.draw(0) # draws scrol bare, with the handle in the center.
            screen.blit(controls, controlsPos)        

        pygame.display.flip() # show changes    
        
    clock.tick(120) # to save on CPU use


 



    
