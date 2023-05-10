from typing import Callable
import logging

import imgui as im
import imgui.glfw as glfw

log = logging.getLogger("CM Window")


class CMWindow:

    def __init__(self, width: int, height: int, title: str) -> None:
        self.window = glfw.Init(
            window_width=width, window_height=height, title=title
        )

        if self.window is None:
            msg = "Error during GLFW init, unable to open window"
            log.fatal(msg)
            raise RuntimeError(msg)

        im.CreateContext()
        glfw.InitContextForGLFW(self.window)
        im.StyleColorsDark()
        self.clearColor = im.Vec4(0.45, 0.55, 0.6, 1.0)

    def run(self, renderFunc: Callable[[], None]):
        while True:
            glfw.NewFrame()
            im.NewFrame()

            renderFunc()

            im.Render()
            glfw.Render(self.window, self.clearColor)

            if glfw.ShouldClose(self.window):
                break

        im.DestroyContext()
        glfw.Shutdown(self.window)