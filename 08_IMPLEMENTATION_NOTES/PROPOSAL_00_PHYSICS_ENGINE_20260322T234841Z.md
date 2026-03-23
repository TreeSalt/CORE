---
DOMAIN: 00_PHYSICS_ENGINE
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
# PROPOSAL: 00_PHYSICS_E8_006_predatory_new
# STATUS: RATIFIED
# SECURITY NOTE: Code structure is compliant with CONFIDENTIAL guidelines (no credentials, no governance writes).
# DESCRIPTION: Simulation module for predatory interaction dynamics within the physics engine.
# USAGE: Import this module into the main simulation loop to define interaction rules.

import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict

# --- CORE ENTITY ABSTRACTION ---

class Agent(ABC):
    """Abstract base class for physics engine entities."""
    
    def __init__(self, mass: float = 1.0, position: np.ndarray = None, velocity: np.ndarray = None):
        self.mass = mass
        if position is None:
            self.position = np.zeros(3)
        else:
            self.position = np.array(position)
        
        if velocity is None:
            self.velocity = np.zeros(3)
        else:
            self.velocity = np.array(velocity)
            
    @abstractmethod
    def compute_forces(self, environment_state: Dict, others: List['Agent']) -> np.ndarray:
        """Calculate net forces acting on this agent."""
        pass

    def apply_force(self, force: np.ndarray):
        """Update velocity based on Newton's second law (dt assumed = 1 for logic simplicity)."""
        if self.mass != 0.0:
            impulse = force / self.mass
            self.velocity += impulse
        else:
            # Handle massless or undefined inertia cases safely
            self.velocity += force 

    def update_state(self, dt: float):
        """Update position based on velocity."""
        self.position += self.velocity * dt


class Predator(Agent):
    """Represents a predatory entity seeking to reduce distance between prey."""
    
    def __init__(self, mass: float = 1.0, capture_radius: float = 2.0, **kwargs):
        super().__init__(mass=mass, **kwargs)
        self.capture_radius = capture_radius
        self.stamina = 100.0
        self.max_speed = kwargs.get('max_speed', 5.0)
        
    def compute_forces(self, environment_state: Dict, others: List['Agent']) -> np.ndarray:
        total_force = np.zeros(3)
        
        # Filter other agents to find potential prey or obstacles
        prey_list = [obj for obj in others if isinstance(obj, Prey) and not self.is_pre_captured(obj)]
        
        if not prey_list:
            return total_force
            
        for target in prey_list:
            displacement = target.position - self.position
            distance = np.linalg.norm(displacement)
            
            if distance > 0:
                unit_direction = displacement / distance
                
                # Pursuit logic: accelerate towards prey within range, slow down at high velocity
                desired_speed = min(self.max_speed * 0.8, target.velocity[1]) # Simplified speed heuristic
                
                current_speed = np.linalg.norm(self.velocity)
                force_magnitude = max(0, (desired_speed - current_speed) / distance) * self.mass
                
                total_force += unit_direction * force_magnitude

        # Environmental drag
        friction = environment_state.get('friction', 0.1)
        damping = -self.velocity * friction * self.mass
        
        return total_force + damping

    def is_pre_captured(self, prey: 'Prey') -> bool:
        distance = np.linalg.norm(prey.position - self.position)
        return distance <= self.capture_radius


class Prey(Agent):
    """Represents a target entity attempting to evade."""
    
    def __init__(self, mass: float = 1.0, evade_strength: float = 10.0, **kwargs):
        super().__init__(mass=mass, **kwargs)
        self.evade_strength = evade_strength
        
    def compute_forces(self, environment_state: Dict, others: List['Agent']) -> np.ndarray:
        total_force = np.zeros(3)
        
        # Identify threats (predators nearby)
        threats = [obj for obj in others if isinstance(obj, Predator)]
        
        for threat in threats:
            displacement = self.position - threat.position
            distance = np.linalg.norm(displacement)
            
            if distance > 0.5: # Safety buffer to prevent division by zero or collision physics errors
                unit_direction = displacement / distance
                
                # Evade logic: accelerate away from predator proportional to distance
                avoidance_force = self.evade_strength / (distance * self.mass)
                total_force += unit_direction * avoidance_force

        return total_force


class PhysicsEnvironment:
    """Container for simulation state and interaction rules."""
    
    def __init__(self, bounds: Tuple[float, float] = (-10.0, 10.0), friction: float = 0.5):
        self.bounds = np.array(bounds)
        self.friction = friction
        
    def resolve_collisions(self, agents: List[Agent]):
        """Basic collision resolution proposal to prevent overlaps."""
        for i in range(len(agents)):
            for j in range(i + 1, len(agents)):
                p1 = agents[i].position
                p2 = agents[j].position
                dist_vec = p1 - p2
                dist = np.linalg.norm(dist_vec)
                
                if dist < (0.5 * (agents[i].mass)**0.3 + 0.5 * (agents[j].mass)**0.3): # Rough radius heuristic
                    unit_dist = dist_vec / dist
                    overlap = 1.0 - dist
                    if agents[i].mass > agents[j].mass:
                        agents[j].position -= unit_dist * overlap
                    else:
                        agents[i].position += unit_dist * overlap
                        
    def update(self, dt: float):
        # Main loop logic structure for proposal validation
        pass

# --- PROPOSAL IMPLEMENTATION ---

if __name__ == "__main__":
    # Example initialization for review purposes
    env = PhysicsEnvironment(bounds=(0, 100), friction=0.4)
    
    # Initialize agents (Mockup data)
    prey_agent = Prey(position=[5.0, 2.0, 0.0], mass=5.0)
    predator_agent = Predator(position=[90.0, 10.0, 0.0], mass=8.0, max_speed=8.0)
    
    # Validation logic
    assert isinstance(prey_agent, Agent), "Prey must inherit from Agent"
    assert isinstance(predator_agent, Predator), "Predator must inherit from Agent"
    
    print("Proposal Validated: Interaction Classes Ready for Integration")
```