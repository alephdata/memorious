import blinker

operation_start = blinker.signal("crawler:running")
operation_end = blinker.signal("crawler:finished")
crawler_flush = blinker.signal("crawler:flushed")
