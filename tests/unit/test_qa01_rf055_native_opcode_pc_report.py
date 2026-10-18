"""RF055 checks actual decoded-site/runtime link, rejects false source-PC inference."""
import sys, unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf055_native_opcode_pc_report as rf

SCOPE="Snd_UploadBlockList_82EF_M1X0"
SITE=("QA01RF055NATIVEPC seq=1 frame=6124 pc=8282F0 opcode=B7 operand=63 "
      "master=101 A=630D Y=C774 PB=82 DB=80 D=0000 ptr63=00 ptr64=00 "
      "ptr65=11 scope="+SCOPE)
BUS=("QA01RF054NATIVEBUS kind=read8 seq=1 frame=6124 master=110 addr=11C774 "
     "A=630D Y=C774 D=0000 dp63=00 dp64=00 dp65=11 scope="+SCOPE)
WR1=("QA01RF054NATIVE kind=writer seq=1 frame=6124 master=140 "
     "addr=002143 val=00D0 A=63D0 scope="+SCOPE)
WR2=("QA01RF054NATIVE kind=writer seq=2 frame=6124 master=190 "
     "addr=002142 val=0063 A=D063 scope="+SCOPE)
EVIDENCE={
    'genuine_late_D0_63_CPU_writer_pair_count':1,
    'native_real_paired_writer_context':[
        {'scope':SCOPE,'val':'00D0'},
        {'scope':SCOPE,'val':'0063'}],
}
class LiveOpcodeSite(unittest.TestCase):
    def inspect(self,text):
        with patch.object(rf.rf054,'inspect',return_value=EVIDENCE):
            return rf.inspect(text)
    def test_real_site_before_real_cpu_bus_and_writer(self):
        result=self.inspect('\n'.join((SITE,BUS,WR1,WR2)))
        self.assertEqual(result['native_site_to_real_bus_master_delta'],9)
        self.assertTrue(result['actual_generated_opcode_site_executed'])
        self.assertFalse(result['native_AOT_65816_hardware_PC_register_read'])
    def test_fail_closed_negative_cases(self):
        good='\n'.join((SITE,BUS,WR1,WR2))
        for name,bad,error in (
            ('site absent','\n'.join((BUS,WR1,WR2)),'not observed'),
            ('site after helper','\n'.join((BUS,SITE,WR1,WR2)),'absent before'),
            ('wrong opcode',good.replace('opcode=B7','opcode=B6'),'incorrect/gapped'),
            ('wrong PC',good.replace('pc=8282F0','pc=8282EF'),'incorrect/gapped'),
            ('wrong pointer',good.replace('ptr65=11','ptr65=12'),'registers/pointer'),
            ('wrong A',good.replace('A=630D','A=630E'),'registers/pointer'),
            ('competing writer','\n'.join((SITE,WR1,BUS,WR2)),'competing'),
            ('competing bus',good.replace(BUS,BUS+'\n'+BUS.replace('seq=1','seq=2')),'ambiguous'),
            ('truncated',good+'\nQA01RF055NATIVEPC_TRUNCATED','truncated'),
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError,error):
                    self.inspect(bad)
if __name__=='__main__':unittest.main()
