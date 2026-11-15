from milestone_guard import assess

def policy():
 return {'milestones':[5,10],'initial_max_updates':10,'next_max_updates':20,'min_legal_rate':.99,'min_retention_rate':.89,'min_samples_per_action':10,'focus_action':'bet','min_relative_ce_gain':.02,'min_target_gain':.02,'extension_target_score':.25}
def window(ce):
 return {'class_balanced_action_ce':ce,'per_action':{a:{'samples':20,'action_ce':ce} for a in ['bet','check','call','fold','raise']}}
def observation():
 return {'completed_updates':10,'checkpoint_id':'ckpt_example','validation':{'checkpoint_updates':10,'legal_rate':1.,'retention_rate':1.,'target_score':.3,'prior_target_score':0.},'action_windows':[window(1.),window(.7)]}
def test_protocol_loss_is_not_used_to_stop_useful_action_learning():
 o=observation();o['aggregate_protocol_loss']=.000001
 assert assess(policy(),o)['action']=='eligible_for_extension'
def test_plateau_requires_action_and_fixed_selection_evidence():
 o=observation();o['action_windows']=[window(.7),window(.699)];o['validation']['prior_target_score']=.3
 assert assess(policy(),o)['action']=='stop'
def test_missing_validation_cannot_spend_another_budget():
 o=observation();o.pop('validation')
 assert assess(policy(),o)['action']=='stop'
def test_learning_loss_cannot_override_legality_regression():
 o=observation();o['validation']['legal_rate']=.9
 assert assess(policy(),o)['action']=='stop'
def test_missing_checkpoint_does_not_destroy_unsaved_work():
 o=observation();o.pop('checkpoint_id')
 assert assess(policy(),o)['action']=='wait'
