from amonpy.tools.angularsep import spcang
import unittest


class TestAngularSep(unittest.TestCase):
  def setUp(self):
    self.pos1 = [83,4]
    self.pos2 = [83,0]
    self.pos3 = [83,22]
    self.pos4 = [86,22]
  
  def tearDown(self):
    pass

  def test_spcang(self):
    s = spcang(self.pos1[0],self.pos2[0],self.pos1[1],self.pos2[1])
    self.assertAlmostEqual(s,4.0,places=4)

    s = spcang(self.pos3[0],self.pos4[0],self.pos3[1],self.pos4[1])
    self.assertAlmostEqual(s,2.78,places=2)

if __name__ == '__main__':
    unittest.main() 
