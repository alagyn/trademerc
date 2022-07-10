from nodepasta.nodegraph import NodeGraph
from cash_money.nodes import *

def registerNodes(nodegraph: NodeGraph):
    nodeTypes = [
        averageTrueRange.AverageTrueRange,
        compareNode.Compare,
        confidenceNode.ConfidenceNode,
        crossoverNode.Crossover,
        delayNode.DelayNode,
        emaNode.EMANode,
        inputNode.InputNode,
        invertNode.InvertNode,
        macdNode.MACD,
        mathNode.MathNode,
        maxCheckNode.MaxCheck,
        minCheckNode.MinCheck,
        parabolicSARNode.ParabolicSAR,
        rangeCheckNode.RangeCheck,
        smaNode.SMANode,
        smmaNode.SMMANode,
        strategyNode.StrategyNode,
        weightNode.WeightNode
    ]

    for t in nodeTypes:
        nodegraph.registerNodeClass(t)
