#! /usr/bin/env python

##########################################################

import pygame
pygame.init() # I don't know what it does or if it is needed for this program
import pygame.freetype 
pygame.freetype.init() # makes font work


import tkinter # tkinter is only used to choose files when loading and saving
import tkinter.filedialog 
tkinter.Tk().withdraw() # stops the save and load dialogue windows from hanging around


from operator import sub
from math import sinh, cosh, tanh, copysign, ceil, log10 # math is nice :)
import random, json, os, sys, subprocess


##########################################################
# Defining graphics options

screenSize = 600, 600 # Initial screen size. Can be changed while running.
universePos = 0, 0 # Position of top left corner of the universe
controlsHeight = 55 # Thickness of control panel.

# A hidden horizontal menu that appear when hovered over
menuPos = 0, 0 # Position of top left corner of menu
menuHeight = 20 # Thickness of menu
menuMargin = 10 # Space between text is 2*menuMarign

'''Since the screen size can change while running the program
this definitions needs to be dynamic'''
def universe_size(screenSize): 
    # Let the Universe fill all space that is not controls
    return screenSize[0], screenSize[1] - controlsHeight
    
def controls_pos(screenSize):
    # Let the controls be at the bottom of the program window
    return 0, screenSize[1] - controlsHeight
    
def controls_size(screenSize):
    # Let the controls be as wide as the program window
    return screenSize[0], controlsHeight
    
controlsPos = controls_pos(screenSize)

font = pygame.freetype.Font(None, 14) # Used for buttons, menu and speed display
bigfont = pygame.freetype.Font(None, 20) # Used for special messages 

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


##########################################################
# Stuff to make Pyinstaller work
# There are probably more fixes needed...

'''
import packaging
import packaging.version
import packaging.specifiers
import packaging.requirements
import appdirs

font = pygame.freetype.Font('/home/tilia/anaconda3/lib/python3.5/site-packages/pygame/freesansbold.ttf', 14)
bigfont = pygame.freetype.Font('/home/tilia/anaconda3/lib/python3.5/site-packages/pygame/freesansbold.ttf', 20)
''' 


##############################################################
# The universe, the objects (points and lines) 
# and the Lorentz-transform

class Universe:
    
    def get_origo(self):
        return self.surface.get_rect().center 
        # objects in the universe will use coordinates centerd at origo
        
    def get_origo_on_screen(self):
        return self.surface.get_rect(topleft = universePos).center
                
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
        self.frame = 0 # Lorentz frame represented by a number     
        self.lines = [] # objects in the universe
        self.points = []  # objects in the universe
        
    def __init__(self, size):
        self.show_lightcone = True # show light-cone as default
        self.surface = pygame.Surface(size) # Here be Universe
        self.clear() # start empty
        
    def draw_in_frame(self, frame):
        ''' draws the universe and all objects in it, 
        in the specified Lorentz frame '''
        self.surface.fill(universeColor)
        
        if self.show_lightcone:
            self.draw_lightcone()
            
        for line in self.lines:
            coords = line.in_other_frame(frame)
                # convert to specified Lorentz frame
            pos = tuple(space_time_to_pixel(self, coord) 
                        for coord in coords)
                # converts to pixel position
            pygame.draw.line(self.surface, line.color(), pos[0], pos[1], lineWidth)
                    
        for point in self.points:
            coord = point.in_other_frame(frame)           
            pos = space_time_to_pixel(self, coord)
            pygame.draw.circle(self.surface, pointColor, pos, pointRadius)

        
    def draw(self): # draws the universe and all objects in it
        self.draw_in_frame(self.frame)
        
    def show(self): # puts the last drawn version of the universe on the screen
        screen.blit(self.surface, universePos)
        
        
def Lorentz_transform(coord, frame_diff): 
    sh, ch = sinh(frame_diff), cosh(frame_diff)
    t, r = coord  
    return (ch*t - sh*r, 
           -sh*t + ch*r)
    

class Point:
    def __init__(self, frame, coord):
        self.coord = coord # space-time coordinate
        self.frame = frame 
            # the Lorentz frame in which the object is defined
        
    def in_other_frame(self, display_frame):
        return Lorentz_transform(self.coord, display_frame - self.frame)
        # gives space-time coordinates in display_frame
        
    
def line_color(coords):
    '''different colors to show if the line is 
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
            # the Lorentz frame in which the object is defined
        self.coords = coords # coordinates for the two end points
        
    def in_other_frame(self, display_frame):
        return tuple(Lorentz_transform(coord, display_frame - self.frame)
                     for coord in self.coords )
    
    def color(self):
        return line_color(self.coords)
        
        
##################################################################
# Relating position on the screen with coordinates in the Universe

def pixel_to_space_time(universe, pos):
    ''' takes pixel position on the screen and gives 
    space-time coordinates in the universe '''
    origo = universe.get_origo()
    t = -(pos[0] - origo[0]) # time coordinate
    r = pos[1] - origo[1] # space coordinate
    return t, r
    
def space_time_to_pixel(universe, coord):
    ''' takes space-time coordinates in universe
    and gives pixel coordinates on universe.surface '''
    origo = universe.get_origo_on_screen()
    x = int(round(origo[0] - coord[0]))
    y = int(round(origo[1] + coord[1]))
    return x, y


##################################################################
# Creating and destroying lines and points

def make_point(universe, pos):
    # takes the pixel position of a point, and makes a point object  
    point = Point(universe.frame, pixel_to_space_time(universe, pos) )
    universe.points.append(point) # adds object to universe content
    universe.draw() # update picture of universe
    return point 
            
def make_line(universe, pos):
    # takes a tuple of two pixel positions and makes a Line object
    coords = tuple(pixel_to_space_time(universe, point) 
                   for point in pos) # convert to space-time coordinates
    line = Line(universe.frame, coords)
    universe.lines.append(line) # adds object to list
    universe.draw() # update picture of universe
    return line
    
    
def straighten_line(start, end): 
    ''' Aids the user in drawing perfectly 
    horizontal, vertical or exactly diagonal line '''
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if abs(dx) < abs(dy)/2:
        return start[0], end[1]
    elif abs(dy) < abs(dx)/2:
        return end[0], start[1]
    else: 
        dx = copysign(dy,dx)
        return start[0] + dx, end[1]
    
def remove(universe, pos):
    ''' removes any point or line in the universe that are on position pos'''
     
    coord = pixel_to_space_time(universe, pos)
    for point in universe.points:
        point_coord = point.in_other_frame(universe.frame)
        dist_sq = (coord[0] - point_coord[0])**2 + (coord[1] - point_coord[1])**2
        if dist_sq <= pointRadius**2:
            universe.points.remove(point)
            return 1 # This return value means that a point was removed
            
    for line in universe.lines:
        line_coords = line.in_other_frame(universe.frame) 
        if line_coords[1][0] - line_coords[0][0] == 0:
            if (coord[0] - line_coords[0][0] <= lineWidth/2
                and coord[1] <= max(line_coords[0][1], line_coords[1][1])
                and coord[1] >= min(line_coords[0][1], line_coords[1][1])):
                universe.lines.remove(line)
                return 2 # This return value means that a line was removed
        
        elif (coord[0] <= max(line_coords[0][0], line_coords[1][0]) + lineWidth/2
            and coord[0] >= min(line_coords[0][0], line_coords[1][0]) - lineWidth/2
            and abs(coord[1] 
                    - (line_coords[0][1] 
                    + (coord[0] - line_coords[0][0])*(line_coords[1][1] - line_coords[0][1])/(line_coords[1][0] - line_coords[0][0]))
                   ) <= lineWidth/2
             ):
            universe.lines.remove(line)
            return 2 # This return value means that a line was removed
    return 0 # This return value means that noting was removed  
    

##################################################################
# Miscellaneous useful stuff

def center(rect, surface):
    ''' returns the pos for putting surface in the center of rect
    good for centering text'''
    return surface.get_rect(center = rect.center).topleft
    

###################################################################
# Menu: Help, Save, Load, Show/Hide light-cone

''' 
This section of the code defines a hidden menu in the top left corner of the screen
which becomes visible when the mouse hovers over this area.
'''


def show_message(text): # will shows message on the screen 
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

def save():
    if not os.path.exists('Saves/'):
        os.mkdir("Saves")
    file = tkinter.filedialog.asksaveasfile(defaultextension=".lor", initialdir = "Saves")
    if file:
        points = [{'frame': point.frame, 'coord': point.coord} for point in universe.points]
        lines = [{'frame': line.frame, 'coords': line.coords} for line in universe.lines]
        json.dump({ 'frame': universe.frame, 
                    'show_lightcone': universe.show_lightcone,
                    'points': points,
                    'lines': lines}, file, indent=4)
        file.close()
          

def load():
    file = tkinter.filedialog.askopenfile(defaultextension=".lor", initialdir = "Saves")
    if file:
        try:
            universe_dict = json.load(file)
            universeSize = universe_size(pygame.display.get_surface().get_rect().size)
            
            global universe # So that I can modify universe
            universe = Universe(universeSize)

            universe.frame = universe_dict['frame']
            universe.show_lightcone = universe_dict['show_lightcone']

            universe.points = [Point(point['frame'], point['coord']) 
                                for point in universe_dict['points']]
                                
            universe.lines = [Line(line['frame'], line['coords'])
                                for line in universe_dict['lines']]
            
        except:
            show_message("Unable to load that file")
                     
        universe.draw()
        

def show_or_hide_lightcone():
    global universe
    universe.show_lightcone = not universe.show_lightcone
    universe.draw()
    universe.show()
    draw_menu(event.pos)


class MenuButton:
    def __init__(self, name, pos, effect):
        text, rect = font.render(name, textColor) # render label text
        self.text = text
        self.rect = pygame.Rect(pos, (rect.width + menuMargin, menuHeight)) 
            # Button area
        self.textpos = center(self.rect, self.text) # text in the center        
        self.effect = effect # what happens when clicked
        
    def draw(self, pos):
        if self.rect.collidepoint(pos):
            pygame.draw.rect(screen, menuActiveColor, self.rect)
        else:
            pygame.draw.rect(screen, menuColor, self.rect)
        screen.blit(self.text, self.textpos)
        
    def do(self):
        self.effect()

menu_options = (("Help", help), # menu options (label, effect)
                ("Save", save), 
                ("Load", load), 
                ("Show/Hide light-cone", show_or_hide_lightcone))
                
menu_list = [] # List of menu buttons, added when created

next_pos = menuPos # pos of fist menu button
for name, effect in menu_options: # Creates all menu buttons
    menu_button = MenuButton(name, next_pos, effect)
    menu_list.append(menu_button)
    next_pos = menu_button.rect.topright
    
menu_rect = pygame.Rect(menuPos, (next_pos[0] - menuPos[0], 20)) # Menu area

def draw_menu(pos):
    for menu_button in menu_list:
        menu_button.draw(pos)
        

###################################################################
# Creating the GUI 

controls = pygame.Surface(controls_size(screenSize)) # The control panel area

class Button:
    def __init__(self, pos, size, text):
        self.rect = pygame.Rect(pos, size)
        self.text = font.render(text, textColor)[0]
        self.is_active = False
        self.textpos = center(self.rect, self.text)
        
    def draw(self): # draws button on screen
        if self.is_active:
            pygame.draw.rect(controls, activeButtonColor, self.rect)
        else:
            pygame.draw.rect(controls, buttonColor, self.rect)
                    
        controls.blit(self.text, self.textpos) # put text on button
    
# Create all buttons
lineButton   = Button((5, 5), (60, 20), "Lines")
pointButton  = Button((5, 30), (60, 20), "Points")
removeButton = Button((70, 5), (60, 20), "Remove") 
clearButton  = Button((70, 30), (60, 20), "Clear")

buttons = (lineButton, pointButton, removeButton, clearButton) # All buttons

drawingOptions = (lineButton, pointButton, removeButton) 
    # These buttons that can not be active simultaneously

class Scroll_bar:
    def __init__(self, pos, size):
        self.rect = pygame.Rect(pos, size)
        self.is_grabed = False
        self.max = int((size[0] - size[1])/2)
        self.handle = pygame.Rect((pos[0] + self.max, pos[1]), (size[1], size[1]))
        self.grab_pos = None # x-pos for wher scrollbar was grabed
           
    def draw(self, shift): 
        ''' draws the scrollbar, 
        where the handle is moved from the center 
        by the length "shift"'''
        pygame.draw.rect(controls, darkGray, self.rect)
        pygame.draw.rect(controls, lightGray, self.handle.move(shift, 0))
        
        
def my_round(frac): 
    ''' round of the speed value to a sensible number of decimals
    this means more decimals when closer to light speed '''
    if abs(frac) < 90:
        return round(frac)
    if abs(frac) < 99:
        return round(frac,1)
    if abs(frac) < 99.9:
        return round(frac,2)
    return round(frac, 2-ceil(log10(100-abs(frac))))
    
        
class Speed_display: # Creates a place to display text
    def __init__(self, pos, size):
        self.rect = pygame.Rect(pos, size)
               
    def hide(self): # Erase any text
        pygame.draw.rect(controls, controlsBgColor, self.rect)    
        
    def show(self, shift): # Shows the relative velocity    
        if self.rect.width < 130:
            text = str(my_round(100 * tanh(0.01 * shift))) + "% c"
                                     
        elif self.rect.width < 290:
            text = str(my_round(100 * tanh(0.01 * shift))) + "% of light speed"
            
        else:         
            text = ("Instantly accelerate to "
                                 + str(my_round(100 * tanh(0.01 * shift)))
                                 + "% of light speed.")
            # Calculate the relative speed and adjust the text depending on avalable space
                                 
        pygame.draw.rect(controls, controlsBgColor, self.rect) # Paint over any old text
        text = font.render(text, textColor)[0] # Render text
        textpos = center(self.rect, text) # Center text
        controls.blit(text, textpos) # Place text on control panel
        
        
scroll_bar = Scroll_bar((138, 8), (screenSize[0] - 138 - 8, 18)) 
    # one scroll bar to specify Lorentz transformations
    
speed_display = Speed_display((138, 8+18), (screenSize[0] - 138 - 8, 55-8-18))
    # one text display to show the related velocity change
    


###################################################################
# Draw the initial view
 
screen = pygame.display.set_mode(screenSize, pygame.RESIZABLE)
    # Creates the program window

universe = Universe(universe_size(screenSize)) # create empty universe 
universe.draw() # draws universe
universe.show() # puts the univeres on screen

controls.fill(controlsBgColor) # paints control panels bacground color
for button in buttons: 
    button.draw() # draws button
scroll_bar.draw(0) # draws scroll bare, with the handle in the center.
screen.blit(controls, controlsPos) # put controls on screen

pygame.display.flip() # update window


###################################################################
# Running the program

clock = pygame.time.Clock() # clock to have clock-ticks, to save on CPU

running = True # Is program running? Assign "False" to quit.


# Global trackers that needs to be updated from inside functions
class Global():
    pass

gl = Global()

gl.is_drawing_line = False # True iff the user in the middle of drawing a line
gl.shift_key_is_down = False # True if the shift key is down
gl.last_pos = (-1, -1) # pos for last MOUSEMOTION event. Put initialy outside screen
gl.last_save_or_load = None # Name of last name file the session is saved or loaded as
gl.start = None # Starting point of line



def in_the_universe(pos): # Check if the point is in the universe
    return (universe.surface.get_rect(topleft=universePos).collidepoint(pos)
            and not menu_rect.collidepoint(pos) )


def left_click_in_menu(pos):
    for button in menu_list:
        if button.rect.collidepoint(pos):
            button.do()
         
 
def left_click_in_the_universe(pos):
    if pointButton.is_active:
        make_point(universe, pos) # make point there
        pygame.draw.circle(screen, pointColor, pos, pointRadius)
            # draw the point
        
    elif lineButton.is_active:
        if not gl.is_drawing_line: # not already marked start of line
            gl.start = pos # remember start of line
            gl.is_drawing_line = True # drawing in progress 
        else:
            end = pos
            if gl.shift_key_is_down:
                end = straighten_line(gl.start, end)
            make_line(universe, (gl.start, end))
            gl.is_drawing_line = False # line is now done
            # no need to draw the line, because it is already there
            
    elif removeButton.is_active:
        remove(universe, pos) # remove anything that is clicked on
        universe.draw() # redraw universe
        universe.show()
            
    
def left_click_on_the_controls(pos):

    if scroll_bar.handle.move(controlsPos).collidepoint(pos): 
        # click on scroll bar handle
        scroll_bar.is_grabed = True
        scroll_bar.grab_pos = pos[0] # save x-pos of where it was garbed
        return

    for button in buttons: # loop all buttons
        if button.rect.move(controlsPos).collidepoint(pos): 
                # check if we are on this button
            button.is_active = not button.is_active # change is active
            button.draw() # re-draw button
            
            if button in drawingOptions:
                for other_button in drawingOptions:
                    if other_button != button:
                        other_button.is_active = False
                        other_button.draw() 
                # can't have more than one of this active at the same time
            
            if gl.is_drawing_line:
                gl.is_drawing_line = False # interrupts any half finished line
                universe.show() # paint over half finished line
                
            screen.blit(controls, controlsPos)    
            break # no need to check other buttons
            
            
def right_ckick(): 
    # the "never mind" action. Interupts what ever is about to happen

    if gl.is_drawing_line: # interrupts any half finished line
        gl.is_drawing_line = False 
        universe.show() # paint over half finished line
    
    elif scroll_bar.is_grabed: # interrupts any Lorentz transformation
        scroll_bar.is_grabed = False # dropp scroll bar
        
        scroll_bar.draw(0) 
        speed_display.hide()
        screen.blit(controls, controlsPos)
        universe.draw() # restore
        universe.show() # redraw
        
    elif clearButton.is_active:
        clearButton.is_active = False # reset button
        clearButton.draw() # redraw button
        screen.blit(controls, controlsPos)
        
        
def left_mouse_button_up(pos): # finalizes clear or scroll
        
    if clearButton.is_active:
        universe.clear() # clear universe
        universe.draw() # redraw universe
        
        universe.show() # paint over half finished line
        clearButton.is_active = False # reset button
        clearButton.draw() # redraw button
        screen.blit(controls, controlsPos)
    
    elif scroll_bar.is_grabed: # finalizes any Lorentz transformation
        scroll_bar.is_grabed = False
        scroll_bar.draw(0)
        universe.frame += 0.01 * (pos[0] - scroll_bar.grab_pos)
        speed_display.hide()
        screen.blit(controls, controlsPos)
        
        
def mouse_motion(pos):
    if scroll_bar.is_grabed:
        shift = pos[0] - scroll_bar.grab_pos
        if shift < -scroll_bar.max:
            shift = -scroll_bar.max
        elif shift > scroll_bar.max:
            shift = scroll_bar.max    
        
        universe.draw_in_frame(universe.frame + 0.01 * shift)
        universe.show()      
            
        scroll_bar.draw(shift)
        speed_display.show(shift)
        screen.blit(controls, controlsPos)
        
    else:     
        if gl.is_drawing_line:
            if in_the_universe(pos):
                end = pos
                if gl.shift_key_is_down:
                    end = straighten_line(gl.start, end)
                universe.show() 
                color = line_color((gl.start, end))
                pygame.draw.line(screen, color, gl.start, end, lineWidth)
                
            elif in_the_universe(gl.last_pos):
                universe.show()
                
        if menu_rect.collidepoint(pos):
            draw_menu(pos)
            
        elif (not gl.is_drawing_line) and menu_rect.collidepoint(gl.last_pos):
            universe.show()
    
    gl.last_pos = pos


while running:
    for event in pygame.event.get(): # what the user is doing
        if event.type == pygame.QUIT:
            #pygame.display.quit() # close window
            running = False # time to stop running program
            break # don't check more events
            
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # a left click
        
            if menu_rect.collidepoint(event.pos): # click in menu
                left_click_in_menu(event.pos) 
        
            elif in_the_universe(event.pos): # a click in universe
                left_click_in_the_universe(event.pos)
                
            else: # a click on the controls
                left_click_on_the_controls(event.pos)        
                        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: 
            right_click()
                               
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            left_mouse_button_up(event.pos)
                    
        elif event.type == pygame.MOUSEMOTION:
            mouse_motion(event.pos)      

                                     
        elif event.type == pygame.KEYDOWN and (event.key == pygame.K_LSHIFT
                                                or event.key == pygame.K_RSHIFT):
            gl.shift_key_is_down = True
            if gl.is_drawing_line:
                end = straighten_line(gl.start, pygame.mouse.get_pos())
                universe.show()
                color = line_color((gl.start, end))
                pygame.draw.line(screen, color, gl.start, end, lineWidth)
                
        elif event.type == pygame.KEYUP and (event.key == pygame.K_LSHIFT
                                            or event.key == pygame.K_RSHIFT):
            gl.shift_key_is_down = False
            if gl.is_drawing_line:
                end = pygame.mouse.get_pos()
                universe.show()
                color = line_color((gl.start, end))
                pygame.draw.line(screen, color, gl.start, end, lineWidth)
                
        elif event.type == pygame.VIDEORESIZE: # resize window
            screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

            universe.surface = pygame.Surface(universe_size(event.size))
            universe.draw()
            universe.show()          
            
            controlsPos = controls_pos(event.size)
            controls = pygame.Surface(controls_size(event.size))
            controls.fill(controlsBgColor)
            for button in buttons: 
                button.draw() # draws button
                
            scroll_bar = Scroll_bar((138, 8), (event.size[0] - 138 - 8, 18)) 
            speed_display = Speed_display((138, 8+18), (event.size[0] - 138 - 8, 55-8-18))
            scroll_bar.draw(0) # draws scroll bare, with the handle in the center.
            screen.blit(controls, controlsPos)        

  
    pygame.display.flip() # show changes    
    clock.tick(120) # to save on CPU use


 



    
