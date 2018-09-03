from freecad_it.test_runner import TestRunner

import lithophane_image_it

testRunner = TestRunner()

testRunner.addTests(lithophane_image_it)

testRunner.run()
