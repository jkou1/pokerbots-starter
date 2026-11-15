"""Regression cases for the actual bare-action monetary scaling defect."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare import scale

def test_bare_preflop_amounts_and_pot_are_all_scaled():
 assert scale('HJ raise 2.0, and BTN raise 7.5. pot 11.0 chips.')=='HJ raise 4, and BTN raise 15. pot 22 chips.'

def test_suffixed_actions_are_not_scaled_twice():
 assert scale('BTN raise 2.5 chips, BB raise 13.0 chips.')=='BTN raise 5 chips, BB raise 26 chips.'

def test_blinds_and_stacks_scale_without_changing_seat_count():
 assert scale('6-handed. small blind 0.5 chips, big blind 1 chips, stacks 100 chips.')=='6-handed. small blind 1 chips, big blind 2 chips, stacks 200 chips.'

def test_fractional_state_is_rejected_instead_of_rounded():
 with pytest.raises(ValueError,match='never rounding'):
  scale('HJ raise 2.3.')
