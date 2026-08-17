// Port of fight_env/player/stats.py.
// The Python version recomputes lazily via dirty flags; here we just recompute
// eagerly whenever equipment changes -- behaviourally identical, simpler.
namespace FightCore
{
    public sealed class Stats
    {
        public string Name;

        private readonly int _baseHp;
        private readonly int _baseStamina;
        private int _hp;
        private int _stamina;

        private Armour _armour = Inventory.ArmourTable[ArmourTypes.NONE];
        private Shield _shield = Inventory.ShieldTable[Shields.NONE];
        private Weapon _weapon = Inventory.WeaponTable[Weapons.NONE];

        private int _weight;
        private int _baseStaminaExpense;

        public Stats(string name = "", int hp = 30, int stamina = 20)
        {
            Name = name;
            _baseHp = hp;
            _baseStamina = stamina;
            _hp = hp;
            _stamina = stamina;
            Recalc();
        }

        public int Hp => _hp;
        public int Stamina => _stamina;

        public Armour Armour => _armour;
        public Shield Shield => _shield;
        public Weapon Weapon => _weapon;

        public void SetArmour(ArmourTypes armour) { _armour = Inventory.ArmourTable[armour]; Recalc(); }
        public void SetShield(Shields shield) { _shield = Inventory.ShieldTable[shield]; Recalc(); }
        public void SetWeapon(Weapons weapon) { _weapon = Inventory.WeaponTable[weapon]; Recalc(); }

        private void Recalc()
        {
            _weight = _armour.Weight + _shield.Weight + _weapon.Weight;
            _baseStaminaExpense = _weight / 5; // Python floor-div; weight >= 0 so identical
        }

        public int BaseStaminaExpense => _baseStaminaExpense;
        public int Weight => _weight;
        public int MaxStamina => _baseStamina - _weight;
        public int MaxHp => _baseHp;
        public int DamageValue => _weapon.BaseDamage;
        public int CriticalDamageValue => _weapon.CriticalDamage;

        // fight_env/player/stats.py :: materialize_event
        public Event MaterializeEvent(Events raw)
        {
            switch (raw)
            {
                case Events.ATTACK:          return new Event(Events.ATTACK, DamageValue);
                case Events.CRITICAL_ATTACK: return new Event(Events.ATTACK, CriticalDamageValue);
                case Events.BLOCK:           return new Event(Events.BLOCK, _shield.Defense);
                default:                     return new Event(raw, 0);
            }
        }
    }
}