from src.simulation import BoidSimulation
if __name__ == "__main__":
    sim = BoidSimulation()
    sim.load_config()
    sim.reset_simulation()
    sim.run_simulation()
    
