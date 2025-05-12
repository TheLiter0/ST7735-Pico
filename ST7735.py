from machine import Pin, SPI
import time

class Screen:
    def __init__(self):
        # SPI Setup
        self.spi = SPI(0, baudrate=20000000, polarity=0, phase=0,
                       sck=Pin(18), mosi=Pin(19))

        # GPIO Pins
        self.cs = Pin(2, Pin.OUT)
        self.dc = Pin(17, Pin.OUT)
        self.rst = Pin(16, Pin.OUT)
        
        self.width = 128
        self.height = 160
        self.framebuffer = bytearray(self.width * self.height * 2)

        # ST7735 OFFSET (confirmed working for many displays)
        self.X_OFFSET = 2
        self.Y_OFFSET = 1

        # Colors in RGB565 format
        self.RED = self.hex_to_rgb565("#FF0000")
        self.BLUE = self.hex_to_rgb565("#0000FF")
        self.GREEN = self.hex_to_rgb565("#008000")
        self.YELLOW = self.hex_to_rgb565("#FFFF00")
        self.CYAN = self.hex_to_rgb565("#00FFFF")
        self.MAGENTA = self.hex_to_rgb565("#FF00FF")
        self.BLACK = self.hex_to_rgb565("#000000")
        self.WHITE = self.hex_to_rgb565("#FFFFFF")
        self.ORANGE = self.hex_to_rgb565("#FFA500")
        self.PURPLE = self.hex_to_rgb565("#800080")

    def write_cmd(self, cmd):
        """Send a command to the display."""
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)

    def write_data(self, data):
        """Send data to the display."""
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(bytearray([data]) if isinstance(data, int) else data)
        self.cs.value(1)

    def reset(self):
        """Reset the display via the reset pin."""
        self.rst.value(0)
        time.sleep_ms(50)
        self.rst.value(1)
        time.sleep_ms(50)

    def set_window(self, x0, y0, x1, y1):
        """Set the window area to draw on the display."""
        x0 += self.X_OFFSET
        x1 += self.X_OFFSET
        y0 += self.Y_OFFSET
        y1 += self.Y_OFFSET
        self.write_cmd(0x2A)  # Column addr
        self.write_data(bytearray([0x00, x0, 0x00, x1]))
        self.write_cmd(0x2B)  # Row addr
        self.write_data(bytearray([0x00, y0, 0x00, y1]))
        self.write_cmd(0x2C)  # Write to RAM

    def fill_screen(self, color):
        """Fill the entire screen with a single color."""
        hi = color >> 8
        lo = color & 0xFF
        for i in range(self.width * self.height):
            self.framebuffer[i * 2] = hi
            self.framebuffer[i * 2 + 1] = lo
        self.update_screen()
    
    def draw_pixel(self, x, y, color):
        """Draw a single pixel at the given coordinates."""
        self.set_window(x, y, x, y)
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(bytearray([color >> 8, color & 0xFF]))
        self.cs.value(1)

    def hex_to_rgb565(self, hex_color):
        """Convert a hex color string to 16-bit RGB565 format."""
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')

        # Convert hex to R, G, B
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        # Convert to RGB565
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        return rgb565
    def update_screen(self):
        """Send the framebuffer to the display."""
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(self.framebuffer)
        self.cs.value(1)

    def init_display(self):
        """Initialize the display with required configuration."""
        self.reset()
        self.write_cmd(0x11)  # Sleep out
        time.sleep_ms(150)
        self.write_cmd(0x3A)  # Color mode
        self.write_data(0x05)  # 16-bit
        self.write_cmd(0x36)  # Memory Access Control (orientation)
        self.write_data(0x00)  # RGB + row/column flip (change from 0x08 to 0x00)
        self.write_cmd(0x29)  # Display on
        time.sleep_ms(100)
        
    def draw_circle(screen, x_center, y_center, radius, color):
        """
        Draws a circle on the screen using the midpoint circle algorithm.

        :param screen: The screen object to draw on.
        :param x_center: The x-coordinate of the circle's center.
        :param y_center: The y-coordinate of the circle's center.
        :param radius: The radius of the circle.
        :param color: The color of the circle in RGB565 format.
        """
        x = 0
        y = radius
        d = 1 - radius  # Decision parameter

        # Helper function to draw the 8 symmetrical points of the circle
        def draw_circle_pixels(x_center, y_center, x, y, color):
            screen.draw_pixel(x_center + x, y_center + y, color)
            screen.draw_pixel(x_center - x, y_center + y, color)
            screen.draw_pixel(x_center + x, y_center - y, color)
            screen.draw_pixel(x_center - x, y_center - y, color)
            screen.draw_pixel(x_center + y, y_center + x, color)
            screen.draw_pixel(x_center - y, y_center + x, color)
            screen.draw_pixel(x_center + y, y_center - x, color)
            screen.draw_pixel(x_center - y, y_center - x, color)

        # Draw the initial points
        draw_circle_pixels(x_center, y_center, x, y, color)

        # Iterate through the circle's octants
        while x < y:
            x += 1
            if d < 0:
                d += 2 * x + 1
            else:
                y -= 1
                d += 2 * (x - y) + 1
            draw_circle_pixels(x_center, y_center, x, y, color)
        

