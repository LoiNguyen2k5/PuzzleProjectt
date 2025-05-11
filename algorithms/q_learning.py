# algorithms/q_learning.py
import random
import time

# --- Q-Learning Parameters (Example, adjust as needed) ---
ALPHA = 0.1  # Learning rate
GAMMA = 0.9  # Discount factor
EPSILON = 0.1 # Exploration rate (for epsilon-greedy)
NUM_EPISODES = 1000 # Number of training episodes
MAX_STEPS_PER_EPISODE = 200 # Max steps per episode to avoid infinite loops

# --- Helper Functions (Specific to 8-Puzzle for Q-Learning) ---
def get_valid_actions(state_tuple):
    """
    Returns a list of possible actions (neighboring states) from the current state.
    Action itself could be the resulting state_tuple.
    """
    state = list(state_tuple)
    try:
        blank_index = state.index(9) # Assuming 9 is the blank tile
    except ValueError:
        return [] # Should not happen in a valid puzzle state

    row, col = divmod(blank_index, 3)
    possible_new_states = []
    moves = [(-1, 0, 'UP'), (1, 0, 'DOWN'), (0, -1, 'LEFT'), (0, 1, 'RIGHT')] # dr, dc, action_name

    for dr, dc, _ in moves:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 3 and 0 <= new_col < 3:
            new_s = state[:]
            new_index = new_row * 3 + new_col
            new_s[blank_index], new_s[new_index] = new_s[new_index], new_s[blank_index]
            possible_new_states.append(tuple(new_s))
    return possible_new_states

def get_reward(state_tuple, goal_state_tuple):
    """
    Calculates the reward for reaching a state.
    """
    if state_tuple == goal_state_tuple:
        return 100  # Large positive reward for reaching the goal
    # elif is_stuck_or_bad_state(state_tuple): # Optional: penalize bad states
    #     return -10
    else:
        return -1   # Small negative reward for each step (encourages shorter paths)

class QLearningAgent:
    def __init__(self, goal_state, alpha=ALPHA, gamma=GAMMA, epsilon=EPSILON):
        self.q_table = {}  # Q-table: state_tuple -> {action_state_tuple: q_value}
        self.goal_state = goal_state
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.training_episodes = 0
        self.nodes_expanded_during_training = 0

    def get_q_value(self, state_tuple, action_state_tuple):
        """Gets Q-value for a state-action pair, defaults to 0 if not seen."""
        return self.q_table.get(state_tuple, {}).get(action_state_tuple, 0.0)

    def choose_action(self, state_tuple):
        """Chooses an action using epsilon-greedy strategy."""
        possible_actions = get_valid_actions(state_tuple)
        if not possible_actions:
            return None # No valid actions from this state

        if random.random() < self.epsilon:
            # Explore: choose a random action
            return random.choice(possible_actions)
        else:
            # Exploit: choose the best action based on Q-values
            q_values = {action: self.get_q_value(state_tuple, action) for action in possible_actions}
            max_q = -float('inf')
            # Handle ties by choosing randomly among best actions
            best_actions = []
            for action, q in q_values.items():
                if q > max_q:
                    max_q = q
                    best_actions = [action]
                elif q == max_q:
                    best_actions.append(action)
            return random.choice(best_actions) if best_actions else None


    def learn(self, state_tuple, action_state_tuple, reward, next_state_tuple):
        """Updates Q-value for a state-action pair."""
        self.nodes_expanded_during_training +=1
        old_q_value = self.get_q_value(state_tuple, action_state_tuple)

        # Find max Q-value for the next state
        next_possible_actions = get_valid_actions(next_state_tuple)
        max_future_q = 0.0
        if next_possible_actions:
            max_future_q = max([self.get_q_value(next_state_tuple, future_action) for future_action in next_possible_actions], default=0.0)
        
        # Q-learning update rule
        new_q_value = old_q_value + self.alpha * (reward + self.gamma * max_future_q - old_q_value)

        if state_tuple not in self.q_table:
            self.q_table[state_tuple] = {}
        self.q_table[state_tuple][action_state_tuple] = new_q_value

    def train(self, start_state_initial, num_episodes=NUM_EPISODES, max_steps_per_episode=MAX_STEPS_PER_EPISODE):
        print(f"Starting Q-Learning training for {num_episodes} episodes...")
        start_train_time = time.time()
        for episode in range(num_episodes):
            # For 8-puzzle, starting from a fixed start_state for each episode might not be diverse enough.
            # Consider starting from various solvable states or shuffling the start_state_initial.
            # For simplicity, we'll use the provided start_state_initial or a random solvable one.
            
            # current_state = start_state_initial # Or generate a random solvable state
            # For now, let's always start from the given initial state for training consistency in this example
            current_state = start_state_initial

            for step in range(max_steps_per_episode):
                action_taken = self.choose_action(current_state)
                if action_taken is None: # No possible moves
                    break 
                
                next_state = action_taken # In this setup, action is the next state
                reward = get_reward(next_state, self.goal_state)
                
                self.learn(current_state, action_taken, reward, next_state)
                current_state = next_state
                
                if current_state == self.goal_state:
                    break # Reached goal
            
            self.training_episodes +=1
            if episode % 100 == 0: # Print progress
                print(f"Episode {episode}/{num_episodes} completed. Q-table size: {len(self.q_table)}")
        
        end_train_time = time.time()
        print(f"Training finished in {end_train_time - start_train_time:.2f} seconds.")
        print(f"Total nodes expanded during training: {self.nodes_expanded_during_training}")


    def get_policy_path(self, start_state_tuple, max_path_length=50):
        """
        Extracts the learned policy (path) from start_state to goal_state.
        """
        path = [start_state_tuple]
        current_state = start_state_tuple
        visited_in_path = {start_state_tuple} # To avoid cycles during path reconstruction

        for _ in range(max_path_length):
            if current_state == self.goal_state:
                break

            possible_actions = get_valid_actions(current_state)
            if not possible_actions:
                print("Warning: No possible actions from state in policy path reconstruction.")
                return None # Stuck

            # Choose the best action based on learned Q-values (exploitation)
            q_values = {action: self.get_q_value(current_state, action) for action in possible_actions}
            
            best_action = None
            max_q = -float('inf')
            
            # Filter out actions leading to already visited states in this path attempt
            # And select the one with the highest Q-value
            candidate_actions = []
            for action, q in q_values.items():
                if action not in visited_in_path:
                    if q > max_q:
                        max_q = q
                        candidate_actions = [action]
                    elif q == max_q:
                        candidate_actions.append(action)
            
            if not candidate_actions: # All next states are already in path, likely a loop or dead end
                 # Try to pick any unvisited neighbor if Q-values led to a cycle
                non_cycle_actions = [act for act in possible_actions if act not in visited_in_path]
                if non_cycle_actions:
                    best_action = random.choice(non_cycle_actions) # Randomly pick if no clear best
                else:
                    print("Warning: Stuck in a loop or dead end during policy path reconstruction.")
                    return None # Cannot proceed

            else:
                best_action = random.choice(candidate_actions) # Randomly choose among best if tie

            if best_action is None:
                print("Warning: Could not determine best_action in policy path reconstruction.")
                return None

            current_state = best_action
            path.append(current_state)
            visited_in_path.add(current_state)
        
        if path[-1] != self.goal_state:
            print("Warning: Policy path did not reach goal state within max_path_length.")
            # Optionally return the partial path or None
            return None 
        
        return path

# Global agent instance (can be problematic for multiple calls without reset, consider instance per solve)
# For simplicity in this example, it's global.
q_agent = None 
is_trained = False

def solve(start_state, goal_state):
    """
    Solves the 8-puzzle using Q-Learning.
    This function will first train a Q-Learning agent (if not already trained
    or if a retrain is desired) and then use the learned policy to find a path.
    """
    global q_agent, is_trained
    
    print(f"Q-Learning: Attempting to solve from {start_state} to {goal_state}")

    # Initialize or re-initialize the agent
    # For a real application, you might want to save/load the Q-table
    # or have a more sophisticated training strategy.
    if q_agent is None or q_agent.goal_state != goal_state: # Re-init if goal changed
        print("Initializing Q-Learning agent.")
        q_agent = QLearningAgent(goal_state=goal_state)
        is_trained = False # Needs retraining if goal changed or first time

    if not is_trained:
        print("Q-table not trained or goal changed. Starting training...")
        # In a real scenario, you might train on a variety of start states.
        # Here, we train starting from the specific `start_state` given.
        # This might overfit the Q-table to this particular start if not handled carefully.
        q_agent.train(start_state_initial=start_state, num_episodes=NUM_EPISODES, max_steps_per_episode=MAX_STEPS_PER_EPISODE)
        is_trained = True
        print("Training complete.")
    else:
        print("Using pre-trained Q-table.")

    # After training, extract the policy (path)
    print("Extracting policy path...")
    path = q_agent.get_policy_path(start_state, max_path_length=100) # Adjust max_path_length as needed

    if path:
        print(f"Q-Learning: Path found with {len(path)-1} steps.")
        # The 'nodes_expanded' for Q-learning is tricky.
        # We can report nodes expanded during training or during policy extraction.
        # For now, let's use nodes expanded during training as a proxy.
        # If Q-learning is used purely for exploitation after training, nodes expanded would be path length.
        nodes_expanded = q_agent.nodes_expanded_during_training
        return path, nodes_expanded
    else:
        print("Q-Learning: No path found or failed to extract policy.")
        return None, q_agent.nodes_expanded_during_training # Return training nodes even if no path found

if __name__ == '__main__':
    # Example Usage (for testing this file directly)
    test_start_state = (1, 8, 2, 9, 4, 3, 7, 6, 5) # A solvable state
    test_goal_state = (1, 2, 3, 4, 5, 6, 7, 8, 9)
    
    print("--- Testing Q-Learning ---")
    
    # First solve: will train
    solution_path, expanded_nodes = solve(test_start_state, test_goal_state)
    if solution_path:
        print("Solution Path:", solution_path)
        print("Expanded Nodes (during training):", expanded_nodes)
    else:
        print("No solution found.")
    
    print("\n--- Second solve (should use trained Q-table if start/goal same) ---")
    # If start_state is different, it will still use the Q-table trained on the first start_state.
    # This highlights a limitation of the current simple global agent setup.
    # test_start_state_2 = (1, 2, 3, 4, 9, 5, 7, 8, 6)
    # solution_path_2, expanded_nodes_2 = solve(test_start_state_2, test_goal_state)
    
    # To demonstrate re-use:
    solution_path_2, expanded_nodes_2 = solve(test_start_state, test_goal_state)
    if solution_path_2:
        print("Solution Path 2:", solution_path_2)
        print("Expanded Nodes (during training, not policy extraction):", expanded_nodes_2) # Will be same as first if not retrained
    else:
        print("No solution found for second solve.")

    # To test with a different goal (will trigger retraining)
    # print("\n--- Third solve (different goal, should retrain) ---")
    # test_goal_state_2 = (9, 1, 2, 3, 4, 5, 6, 7, 8) # A different goal
    # solution_path_3, expanded_nodes_3 = solve(test_start_state, test_goal_state_2)
    # if solution_path_3:
    #     print("Solution Path 3:", solution_path_3)
    #     print("Expanded Nodes (during training):", expanded_nodes_3)
    # else:
    #     print("No solution found for third solve.")