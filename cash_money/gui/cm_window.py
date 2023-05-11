from typing import Callable
import logging

import imgui as im
import imgui.implot as implot
import imgui.glfw as glfw

log = logging.getLogger("CM Window")


def run_window(
    width: int, height: int, title: str, renderFunc: Callable[[], None]
):
    window = glfw.Init(window_width=width, window_height=height, title=title)

    if window is None:
        msg = "Error during GLFW init, unable to open window"
        log.fatal(msg)
        raise RuntimeError(msg)

    im.CreateContext()
    implot.CreateContext()
    glfw.InitContextForGLFW(window)
    im.StyleColorsDark()
    clearColor = im.Vec4(0.45, 0.55, 0.6, 1.0)

    while not glfw.ShouldClose(window):
        glfw.NewFrame()
        im.NewFrame()

        renderFunc()

        im.Render()
        glfw.Render(window, clearColor)

    implot.DestroyContext()
    im.DestroyContext()
    glfw.Shutdown(window)
