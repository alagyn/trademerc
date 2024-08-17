from typing import Callable, Optional
import logging

import imgui as im
from imgui import glfw
import imgui.implot as implot
import imgui.imnodes as imnodes

log = logging.getLogger("CM Window")

# Define a DrawFunc as a callable that takes no arguments and returns a bool
DrawFunc = Callable[[], bool]


def errorCallback(err: int, msg: str) -> None:
    print(f'GLFW Error Code: {err}, Msg: {msg}')


def run_window(
    title: str,
    draw: DrawFunc,
    width: int | None = None,
    height: int | None = None,
    init: Optional[Callable[[], None]] = None,
    cleanup: Optional[Callable[[], None]] = None
):
    """
    Create a single window and enter render loop until either the window is closed
    or the draw() func returns true
    init is called once, after imgui is initialized
    cleanup func is called once before imgui contexts are destroyed
    """

    # set error callback func
    #glfw.SetErrorCallback(errorCallback)
    if not glfw.Init():
        log.fatal("Cannot initialize GLFW")
        raise RuntimeError()

    # create our window
    #glfw.WindowHint(glfw.CONTEXT_VERSION_MAJOR, 4)
    #glfw.WindowHint(glfw.CONTEXT_VERSION_MINOR, 6)
    if width is None or height is None:
        monitor = glfw.GetPrimaryMonitor()
        vidMode = glfw.GetVideoMode(monitor)
        width = vidMode.width
        height = vidMode.height

    window = glfw.CreateWindow(width, height, title)
    if window is None:
        log.fatal("Cannot create GLFW window")
        raise RuntimeError()

    glfw.MakeContextCurrent(window)
    # enable vsync
    glfw.SwapInterval(1)

    # Create ImGui context
    im.CreateContext()
    # optionally create extension contexts
    implot.CreateContext()
    imnodes.CreateContext()

    # Initialize glfw backend
    im.InitContextForGLFW(window, "#version 130")

    # 4) Setup style
    im.StyleColorsDark()
    imnodes.StyleColorsDark()
    # Set background OpenGL "clear color"
    clear_color = im.Vec4(0.45, 0.55, 0.6, 1.0)
    # do any init tasks
    if init is not None:
        init()

    # 5) Main Loop
    while True:
        # pre-frame init
        glfw.PollEvents()
        im.NewFrame()

        # Do GUI processing
        shouldExit = draw()

        # Render the frame
        im.Render(window, clear_color)
        glfw.SwapBuffers(window)

        # if the draw func says we should exit, or the user clicked the close button
        if shouldExit or glfw.WindowShouldClose(window):
            break

    # do any cleanup tasks
    if cleanup is not None:
        cleanup()

    # Shutdown window
    # Do this first, else there will usually be a segfault
    glfw.DestroyWindow(window)

    im.Shutdown()

    # Destroy Contexts
    # in reverse order, destroy extensions first
    imnodes.DestroyContext()
    implot.DestroyContext()
    im.DestroyContext()

    # terminate glfw
    glfw.Terminate()

    # Done
