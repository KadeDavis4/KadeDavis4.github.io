def solve_tsp(G):

    current_node = 0
    visited = []
    result = [0]


    while len(visited) < len(G):
        visited.append(current_node)
        if len(visited) == len(G):
            result.append(0)
            return result

        shortest = float('inf')

        for i in range(len(G[current_node])):
            if i not in visited:
                if G[current_node][i] == 0:
                    continue
                if shortest == float('inf'):
                    shortest = i
                elif G[current_node][i] < G[current_node][shortest]:
                    shortest = i
        current_node = shortest
        result.append(current_node)
        

