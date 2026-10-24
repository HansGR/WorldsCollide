from event.event import *

class FerryBoss(Event):
    """Ruination only: the ferry's sea boss gives an item.

    The sea boss is the Narshe Battle boss (Kefka at Narshe) moved onto the
    ferry; event/ruination.py fix_ferry_connections fights it on the first
    voyage and gives this slot's item right after the battle. The slot is its
    own, so the Narshe Battle check keeps its reward if it ever joins the
    ruination map."""
    def name(self):
        return "Ferry Boss"

    def init_rewards(self):
        if self.args.ruination_mode:
            self.reward = self.add_reward(RewardType.ITEM)

    def mod(self):
        if self.args.ruination_mode:
            self.get_boss("Kefka (Narshe)")     # logs the sea boss when bosses are shuffled
            self.log_reward(self.reward)
