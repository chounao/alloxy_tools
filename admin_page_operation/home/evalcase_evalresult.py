from dataclasses import dataclass
from typing import List, Dict, Tuple, Callable, Optional
import json


# ==================== 一、通用数据结构设计（适配MMLU多任务覆盖+难度分层）====================
@dataclass
class EcommerceEvalCase:
    """电商通用评测用例（支持多任务、难度分层）
    适配任务类型：customer_service(客服答疑)/title_generation(商品标题生成)/category_classification(类目分类)
    难度等级：easy(简单)/medium(中等)/hard(困难)，借鉴MMLU难度分层思路
    """
    case_id: str  # 用例唯一标识
    task_type: str  # 任务类型
    difficulty: str  # 难度等级
    input_data: Dict[str, str]  # 任务输入数据（按任务类型动态定义）
    standard_data: Dict[str, str]  # 标准数据（标准答案/属性）
    language: str = "zh"  # 默认中文，适配C-Eval中文场景


@dataclass
class MultiTurnEvalCase:
    """多轮对话评测用例（适配MT-Bench多轮交互思路）"""
    case_id: str
    task_type: str
    difficulty: str
    turns: List[Dict[str, str]]  # 多轮交互数据：[{"user_query": "用户问题", "system_info": "商品/规则信息"}]
    standard_responses: List[str]  # 每轮标准回复
    language: str = "zh"


@dataclass
class EvalResult:
    """通用评测结果（融合C-Eval主客观评分思路）"""
    case_id: str
    task_type: str
    difficulty: str
    model_output: str  # 模型输出（单轮为字符串，多轮为列表转字符串）
    objective_scores: Dict[str, float]  # 客观评分（准确性、完整性等可量化维度）
    subjective_scores: Dict[str, float]  # 主观评分（友好性、吸引力等人为主观维度）
    total_score: float  # 总分（客观分*权重 + 主观分*权重）
    human_feedback: Optional[str] = None  # 人类评估反馈（适配MT-Bench人类评估）


# ==================== 二、评分器基类（模块化设计，支持多任务扩展）====================
class BaseTaskScorer:
    """任务评分器基类，定义统一评分接口，不同任务继承实现"""

    def __init__(self, objective_weight: float = 0.7, subjective_weight: float = 0.3):
        self.objective_weight = objective_weight  # 客观分权重
        self.subjective_weight = subjective_weight  # 主观分权重

    def compute_objective_scores(self, model_output: str, standard_data: Dict[str, str]) -> Dict[str, float]:
        """计算客观评分（子类必须实现）"""
        raise NotImplementedError("需在子类中实现客观评分计算")

    def compute_subjective_scores(self, model_output: str, human_annotations: Optional[Dict[str, float]] = None) -> \
    Dict[str, float]:
        """计算主观评分（支持人工标注或自动判断）"""
        if human_annotations:
            return human_annotations
        return {"default_subjective": 0.0}  # 无人标注时默认0分

    def compute_total_score(self, objective_scores: Dict[str, float], subjective_scores: Dict[str, float]) -> float:
        """计算总分：客观分权重占比 + 主观分权重占比"""
        total_obj = sum(objective_scores.values())
        total_subj = sum(subjective_scores.values())
        return round(total_obj * self.objective_weight + total_subj * self.subjective_weight, 2)

    def score(self, model_output: str, standard_data: Dict[str, str],
              human_annotations: Optional[Dict[str, float]] = None) -> Tuple[Dict[str, float], Dict[str, float], float]:
        """统一评分入口"""
        obj_scores = self.compute_objective_scores(model_output, standard_data)
        subj_scores = self.compute_subjective_scores(model_output, human_annotations)
        total_score = self.compute_total_score(obj_scores, subj_scores)
        return obj_scores, subj_scores, total_score


# ==================== 三、具体任务评分器实现（以客服答疑为例，可扩展其他任务）====================
class CustomerServiceScorer(BaseTaskScorer):
    """客服答疑任务评分器（匹配文档2.3节评分标准）"""

    def compute_objective_scores(self, model_output: str, standard_data: Dict[str, str]) -> Dict[str, float]:
        """计算客观评分：准确性、完整性、简洁性（可量化）"""
        # 1. 准确性评分（0-4分）：核心信息（能否退换、处理时效）匹配度
        accuracy_score = 0.0
        core_infos = [standard_data["can_return"], standard_data["processing_time"]]
        correct_count = sum(1 for info in core_infos if info in model_output)
        if correct_count == 2:
            accuracy_score = 4.0
        elif correct_count == 1:
            accuracy_score = 2.0

        # 2. 完整性评分（0-3分）：辅助信息（所需材料、运费规则）匹配度
        completeness_score = 0.0
        complete_infos = [standard_data["materials"], standard_data["freight_rule"]]
        complete_count = sum(1 for info in complete_infos if info in model_output)
        if complete_count == 2:
            completeness_score = 3.0
        elif complete_count == 1:
            completeness_score = 1.0

        # 3. 简洁性评分（0-1分）：字符数合规性（50字内满分）
        conciseness_score = 0.0
        if len(model_output) <= 50:
            conciseness_score = 1.0
        elif 50 < len(model_output) <= 100:
            conciseness_score = 0.5

        return {
            "accuracy": accuracy_score,
            "completeness": completeness_score,
            "conciseness": conciseness_score
        }

    def compute_subjective_scores(self, model_output: str, human_annotations: Optional[Dict[str, float]] = None) -> \
    Dict[str, float]:
        """计算主观评分：友好性（适配C-Eval中文语义理解）"""
        if human_annotations and "friendliness" in human_annotations:
            return {"friendliness": human_annotations["friendliness"]}

        # 自动判断友好性：基于中文客服常用友好关键词
        friendly_keywords = ["亲", "您好", "麻烦您", "感谢", "哦~"]
        negative_keywords = ["不行", "不知道", "你自己看"]

        if any(keyword in model_output for keyword in negative_keywords):
            return {"friendliness": 0.0}
        elif any(keyword in model_output for keyword in friendly_keywords):
            return {"friendliness": 2.0}
        else:
            return {"friendliness": 1.0}


# ==================== 四、多轮对话评分器（适配MT-Bench多轮交互思路）====================
class MultiTurnCustomerServiceScorer(BaseTaskScorer):
    """多轮客服对话评分器（评估上下文连贯性）"""

    def compute_objective_scores(self, model_outputs: List[str], standard_responses: List[str]) -> Dict[str, float]:
        """多轮客观评分：单轮准确性 + 上下文连贯性"""
        # 1. 单轮准确性评分（每轮0-2分）
        turn_accuracies = []
        for model_resp, standard_resp in zip(model_outputs, standard_responses):
            # 提取标准回复核心信息（简化为冒号后内容）
            core_info = standard_resp.split("：")[-1] if "：" in standard_resp else standard_resp
            score = 2.0 if core_info in model_resp else 0.0
            turn_accuracies.append(score)

        # 2. 上下文连贯性评分（0-2分）：后一轮是否关联前一轮上下文
        coherence_score = 2.0
        for i in range(1, len(model_outputs)):
            # 过滤短词，判断是否有前一轮核心词汇关联
            prev_keywords = [word for word in model_outputs[i - 1].split() if len(word) > 2]
            if not any(keyword in model_outputs[i] for keyword in prev_keywords):
                coherence_score = 0.0
                break

        return {
            "turn_accuracies": turn_accuracies,
            "average_accuracy": round(sum(turn_accuracies) / len(turn_accuracies), 2) if turn_accuracies else 0.0,
            "coherence": coherence_score
        }

    def compute_subjective_scores(self, model_outputs: List[str],
                                  human_annotations: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """多轮主观评分：整体流畅性"""
        if human_annotations and "overall_fluidity" in human_annotations:
            return {"overall_fluidity": human_annotations["overall_fluidity"]}

        # 自动判断流畅性：无语气异常（如结尾多问号、连续感叹号）
        fluidity_score = 2.0
        for resp in model_outputs:
            if resp.endswith("？") or "！！！" in resp:
                fluidity_score -= 1.0
        return {"overall_fluidity": max(fluidity_score, 0.0)}

    # 重写score方法，适配多轮输出列表
    def score(self, model_outputs: List[str], standard_responses: List[str],
              human_annotations: Optional[Dict[str, float]] = None) -> Tuple[Dict[str, float], Dict[str, float], float]:
        obj_scores = self.compute_objective_scores(model_outputs, standard_responses)
        subj_scores = self.compute_subjective_scores(model_outputs, human_annotations)
        total_score = self.compute_total_score(obj_scores, subj_scores)
        return obj_scores, subj_scores, total_score


# ==================== 五、评测管理器（统一调度，支持多任务/多轮/批量评测）====================
class EcommerceEvalManager:
    """电商评测管理器（适配MMLU多任务批量评测）"""

    def __init__(self):
        self.scorers = {}  # 任务评分器映射：{task_type: scorer_instance}

    def register_scorer(self, task_type: str, scorer: BaseTaskScorer):
        """注册任务评分器"""
        self.scorers[task_type] = scorer

    def single_case_eval(self, case: EcommerceEvalCase, model_predict: Callable,
                         human_annotations: Optional[Dict[str, float]] = None) -> EvalResult:
        """单条用例评测（支持多难度）"""
        if case.task_type not in self.scorers:
            raise ValueError(f"未注册任务类型：{case.task_type}")

        # 调用模型获取输出
        model_output = model_predict(case.input_data)

        # 调用评分器评分
        scorer = self.scorers[case.task_type]
        obj_scores, subj_scores, total_score = scorer.score(
            model_output=model_output,
            standard_data=case.standard_data,
            human_annotations=human_annotations
        )

        return EvalResult(
            case_id=case.case_id,
            task_type=case.task_type,
            difficulty=case.difficulty,
            model_output=model_output,
            objective_scores=obj_scores,
            subjective_scores=subj_scores,
            total_score=total_score,
            human_feedback=human_annotations.get("feedback") if human_annotations else None
        )

    def multi_turn_eval(self, multi_case: MultiTurnEvalCase, model_multi_predict: Callable,
                        human_annotations: Optional[Dict[str, float]] = None) -> EvalResult:
        """多轮用例评测（适配MT-Bench）"""
        if multi_case.task_type not in self.scorers:
            raise ValueError(f"未注册任务类型：{multi_case.task_type}")

        # 调用多轮模型获取输出列表
        model_outputs = model_multi_predict(multi_case.turns)

        # 调用多轮评分器评分
        scorer = self.scorers[multi_case.task_type]
        obj_scores, subj_scores, total_score = scorer.score(
            model_outputs=model_outputs,
            standard_responses=multi_case.standard_responses,
            human_annotations=human_annotations
        )

        return EvalResult(
            case_id=multi_case.case_id,
            task_type=multi_case.task_type,
            difficulty=multi_case.difficulty,
            model_output=str(model_outputs),
            objective_scores=obj_scores,
            subjective_scores=subj_scores,
            total_score=total_score,
            human_feedback=human_annotations.get("feedback") if human_annotations else None
        )

    def batch_eval(self, cases: List[EcommerceEvalCase], model_predict: Callable,
                   human_annotations_list: Optional[List[Dict[str, float]]] = None) -> List[EvalResult]:
        """批量评测（支持多任务混合评测，借鉴MMLU）"""
        results = []
        human_annotations_list = human_annotations_list or [None] * len(cases)
        for case, annotations in zip(cases, human_annotations_list):
            result = self.single_case_eval(case, model_predict, annotations)
            results.append(result)
        return results


# ==================== 六、测试运行示例 ====================
if __name__ == "__main__":
    # 1. 初始化评测管理器并注册评分器
    eval_manager = EcommerceEvalManager()
    # 注册单轮客服答疑评分器（主客观权重7:3）
    eval_manager.register_scorer(
        task_type="customer_service",
        scorer=CustomerServiceScorer(objective_weight=0.7, subjective_weight=0.3)
    )
    # 注册多轮客服答疑评分器（主客观权重6:4，更侧重用户体验）
    eval_manager.register_scorer(
        task_type="multi_turn_customer_service",
        scorer=MultiTurnCustomerServiceScorer(objective_weight=0.6, subjective_weight=0.4)
    )

    # 2. 构造单轮测试用例（中等难度，来自文档2.3节示例）
    single_case = EcommerceEvalCase(
        case_id="CS_001",
        task_type="customer_service",
        difficulty="medium",
        input_data={
            "user_question": "我买的这款羽绒服收到后发现拉链不顺畅，能退换货吗？大概需要多久能处理完？",
            "product_info": "羽绒服，支持7天无理由退换货（未穿过、未洗涤、吊牌完整）",
            "platform_rules": "退货申请提交后，商家需在24小时内审核，审核通过后消费者寄回商品，商家签收后48小时内退款，往返运费由商家承担（质量问题）"
        },
        standard_data={
            "can_return": "能退换（质量问题）",
            "processing_time": "审核24小时+退款48小时",
            "materials": "吊牌完整、未使用证明",
            "freight_rule": "往返运费由商家承担"
        }
    )

    # 3. 构造多轮测试用例（高难度，模拟真实多轮咨询场景）
    multi_turn_case = MultiTurnEvalCase(
        case_id="MCS_001",
        task_type="multi_turn_customer_service",
        difficulty="hard",
        turns=[
            {"user_query": "这款羽绒服的尺码标准吗？", "system_info": "商品：羽绒服，尺码S-XXL，标准版型"},
            {"user_query": "那如果尺码不合适，能退换吗？", "system_info": "平台规则：7天无理由退换，吊牌完整"},
            {"user_query": "退换需要自己出运费吗？", "system_info": "质量问题运费商家承担，尺码问题运费自理"}
        ],
        standard_responses=[
            "亲，这款羽绒服是标准尺码哦~",
            "尺码不合适可以7天无理由退换，需保证吊牌完整哦~",
            "尺码问题属于非质量问题，往返运费需要您自理呢~"
        ]
    )


    # 4. 模拟模型预测函数（实际使用时替换为真实模型调用，如API调用大模型）
    def mock_single_predict(input_data: Dict[str, str]) -> str:
        """模拟单轮客服模型预测"""
        return "亲，拉链不顺畅属于质量问题可以退换哦~ 退货申请提交后24小时内审核，商家签收后48小时内退款，往返运费由商家承担。请确保吊牌完整、商品未使用~"


    def mock_multi_turn_predict(turns: List[Dict[str, str]]) -> List[str]:
        """模拟多轮客服模型预测"""
        return [
            "亲，这款羽绒服是标准尺码哦~",
            "尺码不合适可以7天无理由退换，需要保证吊牌完整呢~",
            "尺码问题的话，往返运费需要您自己承担哦~"
        ]


    # 5. 执行单轮评测（含人工标注示例）
    human_annotations = {
        "friendliness": 2.0,  # 人工标注友好性满分
        "feedback": "回复准确、语气亲切，符合电商客服沟通规范"
    }
    single_result = eval_manager.single_case_eval(
        case=single_case,
        model_predict=mock_single_predict,
        human_annotations=human_annotations
    )
    print("=== 单轮评测结果（适配MMLU/C-Eval） ===")
    print(f"用例ID：{single_result.case_id}")
    print(f"难度等级：{single_result.difficulty}")
    print(f"模型输出：{single_result.model_output}")
    print(f"客观评分（准确性+完整性+简洁性）：{single_result.objective_scores}")
    print(f"主观评分（友好性）：{single_result.subjective_scores}")
    print(f"总分：{single_result.total_score}/10.0")
    print(f"人类反馈：{single_result.human_feedback}\n")

    # 6. 执行多轮评测
    multi_result = eval_manager.multi_turn_eval(
        multi_case=multi_turn_case,
        model_multi_predict=mock_multi_turn_predict,
        human_annotations={"overall_fluidity": 2.0, "feedback": "多轮回复连贯，核心信息无遗漏"}
    )
    print("=== 多轮评测结果（适配MT-Bench） ===")
    print(f"用例ID：{multi_result.case_id}")
    print(f"难度等级：{multi_result.difficulty}")
    print(f"模型多轮输出：{multi_result.model_output}")
    print(f"客观评分（单轮准确性+连贯性）：{multi_result.objective_scores}")
    print(f"主观评分（整体流畅性）：{multi_result.subjective_scores}")
    print(f"总分：{multi_result.total_score}/10.0")
    print(f"人类反馈：{multi_result.human_feedback}")

    # 7. 批量评测示例（多任务混合）
    batch_cases = [single_case]
    batch_results = eval_manager.batch_eval(batch_cases, mock_single_predict, [human_annotations])
    print("\n=== 批量评测结果汇总 ===")
    for res in batch_results:
        print(f"用例ID：{res.case_id}，任务类型：{res.task_type}，总分：{res.total_score}")