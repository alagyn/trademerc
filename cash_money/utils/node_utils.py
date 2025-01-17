from typing import Dict, Any

from nodepasta.nodegraph import NodeGraph
from cash_money.nodes import *


def registerNodes(nodegraph: NodeGraph):
    nodeTypes = [
        absoluteValueNode.AbsoluteValueNode,
        averageTrueRange.AverageTrueRange,
        bollingerNode.BollingerNode,
        compareNode.Compare,
        confidenceNode.ConfidenceNode,
        constantNode.ConstantNode,
        crossoverNode.Crossover,
        delayNode.DelayNode,
        emaNode.EMANode,
        inputNode.InputNode,
        invertNode.InvertNode,
        logicNode.LogicNode,
        macdNode.MACD,
        mathNode.MathNode,
        parabolicSARNode.ParabolicSAR,
        rangeCheckNode.RangeCheck,
        smaNode.SMANode,
        smmaNode.SMMANode,
        stochasticNode.Stochastic,
        strategyNode.StrategyNode,
        weightNode.WeightNode
    ]

    for t in nodeTypes:
        nodegraph.registerNodeClass(t)


def newStrat(nodeGraph: NodeGraph):
    i = nodeGraph.addNode(inputNode.InputNode)
    o = nodeGraph.addNode(strategyNode.StrategyNode)
    o.pos.x += 200


def defaultStratData() -> Dict[str, Any]:
    ng = NodeGraph()
    newStrat(ng)

    return {
        "name": "newStrat",
        "graph": ng.getJSON()
    }
