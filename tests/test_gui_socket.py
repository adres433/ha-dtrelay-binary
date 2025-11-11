def test_sim_gui_smoke():
    # smoke test: ensure sim_device_gui.py exists and is importable as a module (no GUI loop run)
    import importlib.util, sys, os
    path = os.path.join(os.path.dirname(__file__), '..', 'sim', 'sim_device_gui.py')
    path = os.path.abspath(path)
    assert os.path.exists(path)
    spec = importlib.util.spec_from_file_location('sim_device_gui', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, 'SimulatorCore') and hasattr(mod, 'SimulatorGUI')
