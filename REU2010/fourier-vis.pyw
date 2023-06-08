#!/usr/bin/env python

from Tkinter import *
import tkFont

import math
import cmath


# PARAMETERS

# Available moduli range from 2 to MAX_MODULUS
MAX_MODULUS = 60

# Set definition wraps after WRAP checkboxes
WRAP = 10

# Default size of the drawing area
DEFAULT_CANVAS_WIDTH = 600
DEFAULT_CANVAS_HEIGHT = 400

# Number of pixels corresponding to distance 1
UNIT = 1000

# Draw the unit circle if UNIT_CIRCLE
UNIT_CIRCLE = True

# Draw the x and y-axes if COORDINATE_AXES
COORDINATE_AXES = True

# Display circle of uniformity, of radius equal to linear bias
DISPLAY_EPSILON_CIRCLE = True

# Radius of points in display
DOT_RADIUS = 2

# If True, display all coefficients corresponding to a given modulus
MODULUS_MODE = True

# If True, display the selected coefficient in moduli 2 to MAX_MODULUS
COEFFICIENT_MODE = False


def e(theta):
    return cmath.exp(2*math.pi*1j*theta)

class Translate:
    ORIGIN_CENTER = 0
    ORIGIN_UL = 1
    ORIGIN_UR = 2
    ORIGIN_LL = 3
    ORIGIN_LR = 4

    def renewCoordinates(self):
        # screen has coordinates [0, width - 1], [0, height - 1]
        width, height = self.size_fun()
        if self.origin == Translate.ORIGIN_CENTER:
            origin = (math.trunc((width+1)/2 + 0.5),
                      math.trunc((height+1)/2 + 0.5))
        elif self.origin == Translate.ORIGIN_UL:
            origin = (1, 1)
        elif self.origin == Translate.ORIGIN_UR:
            origin = (width, 1)
        elif self.origin == Translate.ORIGIN_LL:
            origin = (1, height)
        elif self.origin == Translate.ORIGIN_LR:
            origin = (width, height)

        # output range
        self.r_min = (1, 1)
        self.r_max = (width, height)
        # input domain
        self.d_min = ((self.r_min[0]-origin[0])/float(self.unit),
                      (self.r_min[1]-origin[1])/float(self.unit))
        self.d_max = ((self.r_max[0]-origin[0])/float(self.unit),
                      (self.r_max[1]-origin[1])/float(self.unit))

    def translate(self, x, y):
        '''Translate logical coordinates into fixed screen coordinates.'''
        # translate coordinates
        x0 = ((x - self.d_min[0]) / (self.d_max[0]-self.d_min[0])
              * (self.r_max[0] - self.r_min[0]))

        x = self.r_min[0] + math.trunc(
            (x - self.d_min[0]) / (self.d_max[0]-self.d_min[0])
            * (self.r_max[0] - self.r_min[0]) + .5)
        y = self.r_min[1] + math.trunc(
            (y - self.d_min[1]) / (self.d_max[1]-self.d_min[1])
            * (self.r_max[1] - self.r_min[1]) + .5)
        if self.flip:
            y = (self.r_max[1] + self.r_min[1]) - y
        return x, y

    def __init__(self, size_fun, origin = ORIGIN_UL, unit = 1, flip = False):
        # function returning (width, height) of visible drawing area
        self.size_fun = size_fun
        # origin of logical coordinates as a screen coordinate or specifier
        self.origin = origin
        # size of coordinate unit in screen pixels
        self.unit = unit
        # flip y-axis?
        self.flip = flip
        # initialize coordinates
        self.renewCoordinates()


class FourierVis:

    def callback(self, widget, data):
        self.cb_draw_area(self.drawingArea, None)

    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def cond_update_canvas(self):
        if self.redraw:
            self.update_canvas()

    def update_canvas(self):
        # parameters
        aux_dash_length = 7
        aux_dash_spec = (aux_dash_length, aux_dash_length)
        aux_width = 1
        unit_circle_color = "blue"
        epsilon_circle_color = "#3f3f3f"
        coordinate_axes_color = "blue"
        text_color = "blue"
        focus_dot_color = "white"

        # prepare for new drawing
        self.canvas.delete(ALL)
        self.trans.renewCoordinates()

        # constants
        width, height = self.canvasSize()
        origin_x, origin_y = self.trans.translate(0, 0)
        mod = self.N_modulus.get()
        dot = self.N_coeff.get()
        unit = math.trunc(self.trans.unit + .5)

        # objects
        canvas = self.canvas

        # coordinate axes
        if COORDINATE_AXES:
            canvas.create_line(
                1, origin_y, width, origin_y,
                fill=coordinate_axes_color,
                dash=aux_dash_spec,
                dashoffset=(-origin_x) % (2*aux_dash_length) + (
                    (aux_dash_length+1)/2),
                width=aux_width)
            canvas.create_line(
                origin_x, 1, origin_x, height,
                fill=coordinate_axes_color,
                dash=aux_dash_spec,
                dashoffset=(-origin_y) % (2*aux_dash_length) + (
                    (aux_dash_length+1)/2),
                width=aux_width)

        # unit circle
        if UNIT_CIRCLE:
            x0, y0 = self.trans.translate(-1.0, 1.0)
            x1, y1 = self.trans.translate( 1.0,-1.0)
            canvas.create_oval(
                x0, y0, x1, y1,
                outline=unit_circle_color,
                dash=aux_dash_spec,
                width=aux_width)

        # coeffs by mod and by base
        coeffs_mod = self.fourierCoefficients(mod)
        coeffs_base = self.fourierCoefficientsByBase(dot)

        # epsilon circle
        if DISPLAY_EPSILON_CIRCLE:
            eps = max(map(abs,coeffs_mod[1:]))
            delta = abs(coeffs_mod[0])
                # display epsilon text
            canvas.create_text(
                5, 3,
                text=("epsilon = %g" % eps),
                fill=text_color,
                anchor="nw")
            canvas.create_text(
                5, 18,
                text=("delta = %g" % delta),
                fill=text_color,
                anchor="nw")
            # draw epsilon circle
            x0, y0 = self.trans.translate(-eps,eps)
            x1, y1 = self.trans.translate(eps, -eps)
            canvas.create_oval(
                x0, y0, x1, y1,
                outline=epsilon_circle_color,
                dash=aux_dash_spec,
                width=aux_width)

        # display all fourier coefficients for current modulus
        if self.mod_mode.get():
            if mod > 2:
                r,  g,  b = 0, 0, 4095
                dr, dg, db = 4095/(mod-2), 0, -(4095/(mod-2))
            else:
                r, g, b = 2047, 0, 2047
                dr = dg = db = 0

            for i in range(mod):
                if i == 0:
                    color = "#%03x%03x%03x" % (0, 4095, 0)
                else:
                    color = "#%03x%03x%03x" % (r, g, b)
                    r += dr; g += dg; b += db
                if i != (dot % mod):
                    x0, y0 = self.trans.translate(coeffs_mod[i].real,
                                                  coeffs_mod[i].imag)
                    canvas.create_oval(
                        x0 - DOT_RADIUS, y0 - DOT_RADIUS,
                        x0 + DOT_RADIUS, y0 + DOT_RADIUS,
                        fill=color,
                        width=0)

        # display current coefficient for all moduli
        if self.coeff_mode.get():
            if self.max_modulus > 2:
                r = g = b = 1023
                dr = dg = db = 2048/(self.max_modulus-2)
            else:
                r = g = b = 2047
                dr = dg = db = 0

            for i in range(self.max_modulus-3):
                color = "#%03x%03x%03x" % (r, g, b)
                r += dr; g += dg; b += db
                if (i+2) != mod:
                    x0, y0 = self.trans.translate(coeffs_base[i].real,
                                                  coeffs_base[i].imag)
                    canvas.create_oval(
                        x0 - DOT_RADIUS, y0 - DOT_RADIUS,
                        x0 + DOT_RADIUS, y0 + DOT_RADIUS,
                        fill=color,
                        width=0)

        # display focus coefficient
        p = dot % mod
        color = focus_dot_color
        x0, y0 = self.trans.translate(coeffs_mod[p].real,
                                      coeffs_mod[p].imag)
        canvas.create_oval(
            x0 - DOT_RADIUS, y0 - DOT_RADIUS,
            x0 + DOT_RADIUS, y0 + DOT_RADIUS,
            fill=color)

    def manage_checkboxes(self):
        N = self.N_modulus.get()
        if N > self.last_modulus:
            for i in range(self.last_modulus, N):
                self.buttons[i]["state"] = "normal"
        else:
            for j in range(N, self.last_modulus):
                self.buttons[j]["state"] = "disabled"
        self.last_modulus = N

    def fourierCoefficients(self, N):
        N = math.trunc(N+0.5)
        M = float(N)
        A = [1 if self.button_vars[i].get() else 0
             for i in range(self.max_modulus)]
        f = lambda n: A[n % N]
        # could substitute other f in here

        E = [e(i/M) for i in range(N)]
        g = lambda n: E[n % N]
        B = [[f(x)*g(-x*k) for x in range(N)] for k in range(N)]
        return map((lambda L: sum(L)/M), B)

    def fourierCoefficientsByBase(self, k):
        k = math.trunc(k+0.5)
        l = float(k)
        A = [1 if self.button_vars[i].get() else 0 for i in range(self.max_modulus)]
        f = lambda n: A[n % N]

        B = [sum([f(x)*e(-x*l/N) for x in range(N)])/N for N in range(2,self.max_modulus)]
        return B

    def getSet(self, modulus = None):
        if modulus == None:
            modulus = self.max_modulus

        set_list = []
        for i in range(modulus):
            if self.button_vars[i].get():
                set_list.append(i)
        return set(set_list)

    def modifySet(self, set_, op):
        vars_ = self.button_vars
        if op == "unset":
            func = lambda var: var.set(False)
        elif op == "set":
            func = lambda var: var.set(True)
        elif op == "toggle":
            func = lambda var: var.set(not var.get())
        else:
            func = lambda var: None

        self.redraw = False
        try:
            for i in set_:
                func(vars_[i])
        finally:
            self.redraw = True
            self.update_canvas()

    def translate(self, amount):
        modulus = self.N_modulus.get()
        set_ = self.getSet(modulus)
        border = []
        for i in set_:
            prev = (i-amount) % modulus
            next = (i+amount) % modulus
            if not prev in set_:
                border.append(i)
            if not next in set_:
                border.append(next)
        border = set(border)
        self.modifySet(border, "toggle")

    def toggleAP(self, start, interval, length):
        modulus = self.N_modulus.get()
        AP = set(map(lambda x: x % modulus,
                     range(start, start+length*interval, interval)))
        self.modifySet(AP, "toggle")
        

    def toggleQuadraticResidues(self):
        modulus = self.N_modulus.get()
        residues = set(map(lambda x: (x**2) % modulus, range(1, modulus)))
        self.modifySet(residues, "toggle")

    def clearSet(self):
        set_ = range(self.max_modulus)
        self.modifySet(set_, "unset")

    def invertSet(self):
        set_ = range(self.max_modulus)
        self.modifySet(set_, "toggle")

    def quitApp(self):
        self.master.destroy()

    def instructions(self):
        if self.help_dialog == None:
            self.help_dialog = FourierInfoPanel(self.master, "info")
            self.help_dialog.wait_window(self.dialog)
            self.help_dialog = None
        else:
            self.help_dialog.lift()
            self.help_dialog.focus_force()

    def about(self):
        if self.about_dialog == None:
            self.about_dialog = FourierInfoPanel(self.master, "about")
            self.about_dialog.wait_window(self.dialog)
            self.about_dialog = None
        else:
            self.about_dialog.lift()
            self.about_dialog.focus_force()

    def arithmeticProgressionUI(self):
        if self.dialog == None:
            result = dict()
            result["proceed"] = False
            self.dialog = APSelector(self.master, result,
                                     self.N_modulus.get())
            self.dialog.wait_window(self.dialog)
            self.dialog = None

            if result["proceed"]:
                start = result["start"]
                step = result["step"]
                length = result["length"]
                if step == 0:
                    length = 1
                    step = 1
                self.toggleAP(start, step, length)
        else:
            self.dialog.lift()
            self.dialog.focus_force()

    def translateUI(self):
        if self.dialog == None:
            result = dict()
            result["proceed"] = False
            self.dialog = TranslateSelector(self.master, result,
                                            self.N_modulus.get())
            self.dialog.wait_window(self.dialog)
            self.dialog = None

            if result["proceed"]:
                amount = result["amount"]
                self.translate(amount)
        else:
            self.dialog.lift()
            self.dialog.focus_force()

    def canvasSize(self):
        coords = self.frame.grid_bbox(0, 0, 1, 0)
        width, height = coords[2], coords[3]
        border_pixels = 2*self.padding + 2*self.canvas_border
        width = width - border_pixels
        height = height - border_pixels
        return width, height

    def __init__(self, master, max_modulus, wrap = 10):
        # GUI parameters
        self.bg = "white"
        self.highlight_color = "gray"
        self.canvas_color = "black"
        self.padding = 3
        self.select_border = 1
        self.canvas_border = 1
        self.max_modulus = max_modulus # consider fourier coefficients in Z_2 to Z_(max_modulus)
        self.wrap = wrap # number of moduli to show before wrapping rows

        # logical parameters
        self.redraw = True # used to turn off re-rendering for mass updates
        self.help_dialog = None
        self.about_dialog = None
        self.dialog = None

        # control variables
        self.N_modulus = IntVar() # int: current modulus
        self.N_modulus.set(max(self.max_modulus/2, 2))
        self.N_coeff = IntVar() # int: current coefficient
        self.N_coeff.set(0)
        self.mod_mode = IntVar() # bool: display all coeffs of modulus?
        self.mod_mode.set(MODULUS_MODE)
        self.coeff_mode = IntVar() # bool: display coeff for all moduli?
        self.coeff_mode.set(COEFFICIENT_MODE)
        self.button_vars = [] # bool: is element i in the current set?
        for i in range(self.max_modulus):
            self.button_vars.append(IntVar())

        # keep track of parent window
        self.master = master

        # top menu
        self.top_menu = Menu(
            self.master)
        self.master["menu"] = self.top_menu

        # file menu
        self.file_menu = Menu(
            self.top_menu,
            tearoff=0)
        self.top_menu.add_cascade(
            menu=self.file_menu,
            label="File")
        self.file_menu.add_command(
            label="Quit",
            command=self.quitApp,
            accelerator="Ctrl+Q",
            underline=0)

        # display menu
        self.display_menu = Menu(
            self.top_menu,
            tearoff=0)
        self.top_menu.add_cascade(
            menu=self.display_menu,
            label="Display")
        self.display_menu.add_checkbutton(
            label="Modulus Mode",
            variable=self.mod_mode)
        self.display_menu.add_checkbutton(
            label="Coefficient Mode",
            variable=self.coeff_mode)

        # set menu
        self.set_menu = Menu(
            self.top_menu,
            tearoff=0)
        self.top_menu.add_cascade(
            menu=self.set_menu,
            label="Set")
        self.set_menu.add_command(
            label="Clear",
            command=self.clearSet,
            accelerator='Ctrl+C',
            underline=0)
        self.set_menu.add_command(
            label="Invert",
            command=self.invertSet,
            accelerator='Ctrl+I',
            underline=0)
        self.set_menu.add_command(
            label="Translate...",
            command=self.translateUI,
            accelerator='Ctrl+T',
            underline=0)

        # toggle menu
        self.toggle_menu = Menu(
            self.set_menu,
            tearoff=0)
        self.set_menu.add_cascade(
            menu=self.toggle_menu,
            label="Toggle")
        self.toggle_menu.add_command(
            label="Arithmetic Progression...",
            command=self.arithmeticProgressionUI)
        self.toggle_menu.add_command(
            label="Quadratic Residues",
            command=self.toggleQuadraticResidues)

        # help menu
        self.help_menu = Menu(self.top_menu, tearoff=0)
        self.top_menu.add_cascade(menu=self.help_menu, label="Help")
        self.help_menu.add_command(
            label="Help",
            command=self.instructions,
            accelerator='F1')
        self.help_menu.add_command(
            label="About",
            command=self.about)
        

        # construct main frame
        self.frame = Frame(
            master,
            bg=self.bg,
            padx=self.padding,
            pady=self.padding)
        self.frame.master.title( "Fourier Coefficients" )
        # (initialize with geometry manager later)

        # modulus slider bar label
        self.modulus_slider_label = Label(
            self.frame,
            text="Modulus:",
            bg=self.bg)
        self.modulus_slider_label.grid(
            row=1, column=0,
            padx=self.padding,
            pady=self.padding,
            sticky=N+E)

        # modulus slider bar
        self.modulus_slider = Scale(
            self.frame,
            variable=self.N_modulus,
            from_=2, to=self.max_modulus,
            orient="horizontal",
            bg=self.bg,
            highlightthickness=self.select_border,
            highlightbackground=self.bg,
            highlightcolor=self.highlight_color)

        self.modulus_slider.grid(
            row=1, column=1,
            columnspan=2,
            sticky=N+S+E+W,
            padx=self.padding)

        # dot slider bar label
        self.dot_slider_label = Label(
            self.frame,
            text="Coefficient:",
            bg=self.bg)
        self.dot_slider_label.grid(
            row=2, column=0,
            padx=self.padding,
            pady=self.padding,
            sticky=N+E)

        # dot slider bar
        self.dot_slider = Scale(
            self.frame,
            variable=self.N_coeff,
            from_=0, to=self.max_modulus-1,
            orient="horizontal",
            bg=self.bg,
            highlightthickness=self.select_border,
            highlightbackground=self.bg,
            highlightcolor=self.highlight_color)

        self.dot_slider.grid(
            row=2, column=1,
            sticky=N+S+E+W,
            padx=self.padding,
            pady=self.padding)

        # drawing area
        self.canvas = Canvas(
            self.frame,
            width=DEFAULT_CANVAS_WIDTH,
            height=DEFAULT_CANVAS_HEIGHT,
            bg=self.canvas_color,
            highlightthickness=self.canvas_border)

        self.canvas.bind("<Configure>", lambda event: self.update_canvas())

        self.canvas.grid(
            row=0, column=0,
            columnspan=2,
            sticky=N+S+E+W,
            padx=self.padding,
            pady=self.padding)

        # coordinate translation
        self.trans = Translate(lambda: self.canvasSize(),
                               Translate.ORIGIN_CENTER, UNIT, True)

        # set definition checkboxes label
        self.set_label = Label(
            self.frame,
            text="Set:",
            bg=self.bg)
        self.set_label.grid(
            row=3, column=0,
            padx=self.padding,
            pady=self.padding,
            sticky=S+E)

        # frame for set definition checkboxes
        self.set_frame = Frame(
            self.frame,
            bg=self.bg)
        self.set_frame.grid(
            row=4, column=1,
            columnspan=1,
            padx=self.padding,
            sticky=N+S+E+W)

        # add check buttons for set definition
        self.buttons = []

        for index in range(self.max_modulus):
            # calculate row and column of button
            grid_row = index / self.wrap
            grid_col = index % self.wrap

            # set row and column to scale in size
            self.set_frame.rowconfigure(grid_row, weight=1)
            self.set_frame.columnconfigure(grid_col, weight=1)

            # define and initialize button
            button = Checkbutton(
                self.set_frame,
                text=("%02d" % index),
                variable=self.button_vars[index],
                bg=self.bg,
                anchor="nw",
                highlightthickness=self.select_border,
                highlightbackground=self.bg,
                highlightcolor=self.highlight_color)

            button.grid(
                row=grid_row, column=grid_col,
                sticky=N+S+E+W)

            self.buttons.append(button)

        # connect control variables to function calls
        self.N_modulus.trace("w", lambda *args: self.cond_update_canvas())
        self.N_modulus.trace("w", lambda *args: self.manage_checkboxes())
        self.N_coeff.trace("w", lambda *args: self.cond_update_canvas())
        self.mod_mode.trace("w", lambda *args: self.cond_update_canvas())
        self.coeff_mode.trace("w", lambda *args: self.cond_update_canvas())

        for i in range(self.max_modulus):
            var = self.button_vars[i]
            var.trace("w", lambda *args: self.cond_update_canvas())

        # connect checkboxes to numAdjustment
        self.last_modulus = self.max_modulus
        self.manage_checkboxes()

        # initialize main frame to make the whole GUI visible
        self.frame.grid(
            row=0, column=0,
            sticky=N+S+E+W)
        self.frame.rowconfigure(0, weight=1)
        # (allow rows 1, 2 and 3 to have natural width)
        # (allow column 0 to have natural width)
        self.frame.columnconfigure(1, weight=1)

        # allow for resizing of window
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        # bind global event bindings
        self.master.bind("<Control-q>", lambda *args: self.quitApp())
        self.master.bind("<Control-Q>", lambda *args: self.quitApp())
        self.master.bind("<Control-c>", lambda *args: self.clearSet())
        self.master.bind("<Control-C>", lambda *args: self.clearSet())
        self.master.bind("<Control-i>", lambda *args: self.invertSet())
        self.master.bind("<Control-I>", lambda *args: self.invertSet())
        self.master.bind("<Control-t>", lambda *args: self.translateUI())
        self.master.bind("<Control-T>", lambda *args: self.translateUI())
        self.master.bind("<F1>",        lambda *args: self.instructions())

    def main(self):
        gtk.main()

class FourierInfoPanel(Toplevel):
    def close(self, args=None):
        self.parent.focus_set()
        self.destroy()

    def __init__(self, parent, type_):
        padding = 6

        if type_ == "info":
            title = "Help"
            label = "Instructions for Usage"
            text = """This program graphically represents the Fourier coefficients of the indicator function of a subset of the integers modulo N for a specified modulus N.

-- Select a modulus using the slider labeled \"Modulus\"
-- Select a coefficient using the slider labeled \"Coefficient\"
-- Specify the set by checking the checkboxes corresponding to elements in the set

The blue circle represents the unit circle, and the gray circle is centered at the origin with radius equal to the linear bias or minimum uniformity of the selected set.  Two display options are available:

-- Modulus Mode: Displays all of the Fourier coefficients of the current set with respect to the selected modulus
-- Coefficient Mode: Displays a single Fourier coefficient of the current set with respect to different moduli

One or both of these options may be active at once.  Options for conveniently modifying the current set are available from the \"Set\" drop-down menu.  It is also possible to modify several other parameters by changing variables prominently located near the top of the source code.  Variables include:

-- MAX_MODULUS: Specifies the range of moduli available for selection
-- WRAP: Specifies how many set selection buttons are displayed per row in the GUI
-- UNIT: Specifies how many pixels correspond to a distance of 1
-- DOT_RADIUS: Specifies the radius, in pixels, of the dots used to represent Fourier coefficients

The application needs to be restarted for changes to the source code parameters to take effect."""
            button = "Close"
        elif type_ == "about":
            title = "About"
            label = "About the Program"
            text = """This program was written and conceived by Bryan Gillespie during the University of Georgia REU in mathematics, Summer 2010.  The REU was run by Professors Neil Lyall and Mariah Hammel, with assistance from graduate student Alex Rice, and centered on the theme of "Structure and Randomness" as it relates to arithmetic combinatorics.  One of the most important tools we used throughout the seven week program was Fourier analysis on the modular integers, and in particular the notion of pseudorandomness which can be seen in sets with uniform non-zero Fourier coefficients.  In order to have a better idea of what it was that we were actually looking at, I wrote this program to graphically visualize the objects we were working with.  See my website at www.epsilonsmall.com for more of my work.

This program is Copyright 2010, Bryan Gillespie, but it is released under a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 license.  That is, you may freely use this program, modify it, and redistribute it, so long as the usage is non-commercial in nature and any derivative work is released only under a Creative Commons or similarly permissive license.  See creativecommons.org for more information."""
            button = "Close"
        else:
            title = "Error Screen"
            label = "Error"
            text = """I'm sorry, but an unrecognized type was specified for this information panel.  If you are seeing this panel, then you've found a bug in the program.  My apologies!  Please contact the author and ask what can be done, or if you have any programming expertise, feel free to look in the source code to see what went wrong."""
            button = "Close"

        Toplevel.__init__(self, parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)

        self.parent = parent

        self.frame = Frame(self)
        self.frame.grid()

        self.label_font = tkFont.Font(
            size=12,
            weight="bold")
        self.label = Label(
            self.frame,
            text=label,
            font=self.label_font)
        self.label.grid(
            row=0, column=0,
            padx=padding,
            pady=padding,
            sticky=W)

        self.text_box = Label(
            self.frame,
            text=text,
            wraplength=600,
            justify="left")
        self.text_box.grid(
            row=1, column=0,
            padx=padding,
            pady=padding,
            sticky=W)

        self.confirm_button = Button(
            self.frame,
            text=button,
            command=self.close,
            default=ACTIVE)
        self.confirm_button.grid(
            row=2, column=0,
            pady=padding)

        self.bind("<Return>", self.close)
        self.bind("<Escape>", self.close)

        # handle window management
        self.focus_set()
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.protocol("WM_DELETE_WINDOW", self.close)


class APSelector(Toplevel):
    def okay(self, args=None):
        self.dictionary["proceed"] = True
        self.dictionary["start"] = self.start_var.get()
        self.dictionary["step"] = self.step_var.get()
        self.dictionary["length"] = self.length_var.get()

        self.parent.focus_set()
        self.destroy()

    def cancel(self, args=None):
        self.dictionary["proceed"] = False

        self.parent.focus_set()
        self.destroy()

    def __init__(self, parent, dictionary, modulus):
        self.dictionary = dictionary
        self.modulus = modulus

        padding = 6

        Toplevel.__init__(self, parent)
        self.title("Specify Arithmetic Progression")
        self.resizable(False, False)
        self.transient(parent)

        self.parent = parent

        # main frame
        self.frame = Frame(self)
        self.frame.grid()
        self.frame.columnconfigure(1, weight=1)

        # title
        self.label_font = tkFont.Font(
            size=12,
            weight="bold")
        self.label = Label(
            self.frame,
            text="Specify Arithmetic Progression",
            font=self.label_font)
        self.label.grid(
            row=0, column=0,
            padx=padding,
            pady=padding,
            sticky=W,
            columnspan=2)

        # description
        self.text_box = Label(
            self.frame,
            text="Please specify a start point, a step size, and a progression length.  Arithmetic progressions are considered in the context of modular arithmetic, so terms are mapped to their appropriate representative between 0 and (modulus - 1) inclusive.",
            wraplength=480,
            justify="left")
        self.text_box.grid(
            row=1, column=0,
            padx=padding,
            pady=padding,
            sticky=W,
            columnspan=2)

        # control variables
        self.start_var = IntVar()
        self.start_var.set(0)
        self.step_var = IntVar()
        self.step_var.set(0)
        self.length_var = IntVar()
        self.length_var.set(3)

        # start point selector
        self.start_label = Label(
            self.frame,
            text="Start Point:")
        self.start_label.grid(
            row=2, column=0,
            sticky=N+E,
            padx=padding,
            pady=padding)

        self.start_slider = Scale(
            self.frame,
            variable=self.start_var,
            from_=0, to=self.modulus-1,
            orient="horizontal")
        self.start_slider.grid(
            row=2, column=1,
            sticky = N+S+E+W,
            padx=padding,
            pady=padding)

        # step size selector
        self.step_label = Label(
            self.frame,
            text="Step Size:")
        self.step_label.grid(
            row=3, column=0,
            sticky=N+E,
            padx=padding,
            pady=padding)

        self.step_slider = Scale(
            self.frame,
            variable=self.step_var,
            from_=-self.modulus+1, to=self.modulus-1,
            orient="horizontal")
        self.step_slider.grid(
            row=3, column=1,
            sticky = N+S+E+W,
            padx=padding,
            pady=padding)

        # progression length selector
        self.length_label = Label(
            self.frame,
            text="Progression Length:")
        self.length_label.grid(
            row=4, column=0,
            sticky=N+E,
            padx=padding,
            pady=padding)

        self.length_slider = Scale(
            self.frame,
            variable=self.length_var,
            from_=1, to=self.modulus,
            orient="horizontal")
        self.length_slider.grid(
            row=4, column=1,
            sticky = N+S+E+W,
            padx=padding,
            pady=padding)

        # buttons
        self.button_frame = Frame(
            self.frame,
            pady=padding)
        self.button_frame.grid(
            row=5, column=0,
            columnspan=2)

        # OK button
        self.confirm_button = Button(
            self.button_frame,
            text="OK",
            command=self.okay,
            default=ACTIVE,
            anchor=E)
        self.confirm_button.grid(
            row=0, column=0,
            padx=padding)

        # Cancel button
        self.cancel_button = Button(
            self.button_frame,
            text="Cancel",
            command=self.cancel,
            anchor=W)
        self.cancel_button.grid(
            row=0, column=1,
            padx=padding)

        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)

        self.bind("<Return>", self.okay)
        self.cancel_button.bind("<Return>", self.cancel)
        self.bind("<Escape>", self.cancel)

        # handle window management
        self.grab_set()
        self.focus_set()
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.protocol("WM_DELETE_WINDOW", self.cancel)

class TranslateSelector(Toplevel):
    def okay(self, args=None):
        self.dictionary["proceed"] = True
        self.dictionary["amount"] = self.amount_var.get()

        self.parent.focus_set()
        self.destroy()

    def cancel(self, args=None):
        self.dictionary["proceed"] = False

        self.parent.focus_set()
        self.destroy()

    def __init__(self, parent, dictionary, modulus):
        self.dictionary = dictionary
        self.modulus = modulus

        padding = 6

        Toplevel.__init__(self, parent)
        self.title("Specify Translation")
        self.resizable(False, False)
        self.transient(parent)

        self.parent = parent

        # main frame
        self.frame = Frame(self)
        self.frame.grid()
        self.frame.columnconfigure(1, weight=1)

        # title
        self.label_font = tkFont.Font(
            size=12,
            weight="bold")
        self.label = Label(
            self.frame,
            text="Specify Translation",
            font=self.label_font)
        self.label.grid(
            row=0, column=0,
            padx=padding,
            pady=padding,
            sticky=W,
            columnspan=2)

        # description
        self.text_box = Label(
            self.frame,
            text="Please specify how much to translate the current set with respect to the current modulus.",
            wraplength=480,
            justify="left")
        self.text_box.grid(
            row=1, column=0,
            padx=padding,
            pady=padding,
            sticky=W,
            columnspan=2)

        # control variables
        self.amount_var = IntVar()
        self.amount_var.set(0)

        # amount selector
        self.amount_label = Label(
            self.frame,
            text="Translate by:")
        self.amount_label.grid(
            row=2, column=0,
            sticky=N+E,
            padx=padding,
            pady=padding)

        self.amount_slider = Scale(
            self.frame,
            variable=self.amount_var,
            from_=-self.modulus+1, to=self.modulus-1,
            orient="horizontal")
        self.amount_slider.grid(
            row=2, column=1,
            sticky = N+S+E+W,
            padx=padding,
            pady=padding)

        # buttons
        self.button_frame = Frame(
            self.frame,
            pady=padding)
        self.button_frame.grid(
            row=5, column=0,
            columnspan=2)

        # OK button
        self.confirm_button = Button(
            self.button_frame,
            text="OK",
            command=self.okay,
            default=ACTIVE,
            anchor=E)
        self.confirm_button.grid(
            row=0, column=0,
            padx=padding)

        # Cancel button
        self.cancel_button = Button(
            self.button_frame,
            text="Cancel",
            command=self.cancel,
            anchor=W)
        self.cancel_button.grid(
            row=0, column=1,
            padx=padding)

        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)

        self.bind("<Return>", self.okay)
        self.cancel_button.bind("<Return>", self.cancel)
        self.bind("<Escape>", self.cancel)

        # handle window management
        self.grab_set()
        self.focus_set()
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.protocol("WM_DELETE_WINDOW", self.cancel)


if __name__ == "__main__":
    root = Tk()
    app = FourierVis(root, MAX_MODULUS, WRAP)
    root.mainloop()
