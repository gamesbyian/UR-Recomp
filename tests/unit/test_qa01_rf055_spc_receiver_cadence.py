"""RF055 read-stage phase is exact, source-dependent and not global clock truth."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf055_spc_receiver_cadence as rf

def synthetic():
    source=[];native=[]
    age=104485209;clock=104485186
    pcs=(('1521','2'),('1525','3'),('1527','2'))
    for i in range(322):
        pc,port=pcs[i%3]
        val=f'{(i//3)%256:02X}'
        source.append(dict(spcpc=pc,port=port,val=val,age=str(age)))
        native.append(dict(pc=pc,port=port,val=val,clock=str(clock)))
        if i<321:
            age+=(5,3,18)[i%3]
            clock+=(5,4,17)[i%3]
    return source,native

class SPCRecipientCadence(unittest.TestCase):
    def test_repeated_real_3_pc_packet_pattern(self):
        source,native=synthetic()
        got=rf.precise_cadence(source,native)
        self.assertEqual(got['verified_complete_three_read_cycles'],107)
        self.assertEqual(got['source_complete_three_read_packet_local_cycles'],26)
        self.assertEqual(got['native_complete_three_read_packet_local_cycles'],26)
        self.assertTrue(got['source_minus_native_322_read_offsets_exact_period_23_23_22'])
        self.assertEqual(got['source_minus_native_read_stage_offset_by_PC']['1527'],{'22':107})
        self.assertFalse(got['equal_CPU_clock_origins_or_global_phase_proven'])
    def test_single_clock_read_or_payload_corruption_fails_closed(self):
        a,b=synthetic()
        for what,index,key,val in [
            ('native late F7',1,'clock','104485192'),
            ('native changed F6 byte',7,'val','FE'),
            ('source different PC',3,'spcpc','1527'),
            ('source read delayed',13,'age','104485341'),
            ('native origin moved',0,'clock','104485185'),
        ]:
            x=[dict(t) for t in a];y=[dict(t) for t in b]
            tgt=x if key in ('spcpc','age') else y
            tgt[index][key]=val
            with self.subTest(what=what),self.assertRaisesRegex(ValueError,'RF055'):
                rf.precise_cadence(x,y)
    def test_missing_or_surplus_instruction_never_qualifies(self):
        a,b=synthetic()
        for x,y in [(a[:-1],b[:-1]),(a,b[:-1]),(a+a[:1],b+b[:1])]:
            with self.assertRaisesRegex(ValueError,'322'):
                rf.precise_cadence(x,y)
if __name__=='__main__': unittest.main()
