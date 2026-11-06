"""Borderless opaque surfaces with child-local painting and explicit role binding."""
from dataclasses import dataclass
from .drawing import Canvas,Rect
@dataclass
class Surface:
    role:str='surface'
    def draw(self,canvas:Canvas,bounds:Rect,painter):
        for v in (bounds.x,bounds.y,bounds.width,bounds.height):
            if type(v)is not int or not 0<=v<=1_000_000:raise ValueError('invalid surface bounds')
        child=Canvas(bounds.width,bounds.height,canvas.palette,self.role)
        painter(child)
        canvas.blit(child,Rect(0,0,bounds.width,bounds.height),bounds.x,bounds.y)
