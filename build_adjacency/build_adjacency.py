import math
import numpy as np
from convert_to_multi import *
import argparse
import random
from scipy import io, sparse
import pdb

def inverse_op(pose, cov):
    """
    Compute x_ji given x_ij
    Input: A 3x1 pose vector [x, y, phi]
           The covariance matrix Cov of that pose, cov is a np array
    """
    x, y, phi = pose
    new_pose = [-x*math.cos(phi)-y*math.sin(phi),
                x*math.sin(phi)-y*math.cos(phi),
                -phi]
    J_minus = np.matrix([[-math.cos(phi), -math.sin(phi), y], \
                         [math.sin(phi), -math.cos(phi), -x], \
                         [0,              0,             -1]])
    new_cov = np.matmul(np.matmul(J_minus, cov), np.transpose(J_minus))
    return new_pose, new_cov

def compound_op(pose1, pose2, cov1, cov2, cov_cross):
    """
    Compute pose1 circle+ pose2
    Input: pose1 = [x1, y1, phi1]
           pose2 = [x2, y2, phi2]
    """
    x1, y1, phi1 = pose1
    x2, y2, phi2 = pose2
    new_pose = [x2*math.cos(phi1) - y2*math.sin(phi1) + x1,
                x2*math.sin(phi1) + y2*math.cos(phi1) + y1,
                phi1 + phi2]
    prev_cov = np.matrix([[cov1,                 cov_cross],
                          [np.transpose(cov_cross),   cov2]])
    J_plus = np.matrix([[1, 0, -(new_pose[1]-y1), math.cos(phi1), -math.sin(phi1), 0], \
                        [0, 1, (new_pose[0]-x1), math.sin(phi1), -math.cos(phi1),  0], \
                        [0, 0,       1,              0,               0,           1]])
    new_cov = np.matmul(np.matmul(J_plus, prev_cov), np.transpose(J_plus))
    return new_pose, new_cov

def compute_mahalanobis_distance():
    pass


class AdjacencyMatrix:
    def __init__(self, multi_graph, gamma=0.5):
        self.gamma = gamma
        self.graph = multi_graph
        self.inter_lc_N = len(multi_graph.inter_lc)

    def build_adjacency_matrix(self):
        adjacency_matrix = np.zeros((self.inter_lc_N, self.inter_lc_N))
        for i in range(self.inter_lc_N):
            adjacency_matrix[i, i] = 1
            for j in range(i):
                mahlij = self.compute_mahalanobis_distance(self.graph.inter_lc[i],
                                                         self.graph.inter_lc[j])
                mahlji = self.compute_mahalanobis_distance(self.graph.inter_lc[j],
                                                         self.graph.inter_lc[i])
                if (mahlij <= self.gamma) and (mahlji <= self.gamma):
                    adjacency_matrix[i, j] = 1
                    adjacency_matrix[j, i] = 1

        assert self.check_symmetry(adjacency_matrix)
        print('The size of adjacency matrix is: ')
        print(adjacency_matrix.shape)
        sparse_adj_matrix = sparse.csr_matrix(adjacency_matrix)
        coo_adj_matrix = sparse_adj_matrix.tocoo()
        return coo_adj_matrix

    def check_symmetry(self, adj_matrix):
        return np.allclose(adj_matrix, np.transpose(adj_matrix))

    def compute_mahalanobis_distance(self, edge1, edge2):
        """
        Input: edge1: Edge object
               edge2: Edge object
        """
        return random.uniform(0,1)
    
    def get_covariance(self):
        return np.random.rand(3,3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build the adjacency matrix given two g2o files")
    parser.add_argument("input_fpath", metavar="input.g2o", type=str,
                        help="g2o file path")
    parser.add_argument("output_fpath", metavar="adjacency.mtx", type=str, nargs='?',
                        default="adjacency.mtx", help="adjacency file path")
    args = parser.parse_args()

    graph = SingleRobotGraph(args.input_fpath)
    multi_graph = graph.to_multi()
    multi_graph.add_random_inter_lc()
    adj = AdjacencyMatrix(multi_graph, 0.5)
    coo_adj_matrix = adj.build_adjacency_matrix()
    io.mmwrite(args.output_fpath, coo_adj_matrix, symmetry='symmetric')