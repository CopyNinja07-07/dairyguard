import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import validate_lin as V

def test_fit_parameters_are_sensible():
    assert 0.025 < V.res["b_ln"] < 0.029 and -10 < V.res["T0_C"] < -8

def test_reproduces_lin_constant_4C_within_10pct():
    assert abs(V.res["h0_at_4C_const_h"] - 90) / 90 < 0.10

def test_reproduces_lin_two_excursion_shelf_life_within_10pct():
    assert abs(V.res["h0_at_4C_two_excursions_h"] - 55) / 55 < 0.10

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("PASS", n)
