// Port of fight_env/inventory/{weapons,shields,armour}.py.
// The numeric stats are load-bearing for combat math; keep them identical.
using System.Collections.Generic;

namespace FightCore
{
    public enum Weapons { NONE, GLADIUS, ZWEIHANDER }
    public enum Shields { NONE, BUCKLER, WOODEN_SHIELD, IRON_SHIELD }
    public enum ArmourTypes { NONE, LIGHT_ARMOUR, HEAVY_ARMOUR }

    public readonly struct Weapon
    {
        public readonly string Name;
        public readonly int BaseDamage;
        public readonly int CriticalDamage;
        public readonly int Weight;
        public Weapon(string name, int baseDamage = 1, int criticalDamage = 3, int weight = 0)
        { Name = name; BaseDamage = baseDamage; CriticalDamage = criticalDamage; Weight = weight; }
    }

    public readonly struct Shield
    {
        public readonly string Name;
        public readonly int Defense;
        public readonly int Weight;
        public Shield(string name, int defense = 0, int weight = 0)
        { Name = name; Defense = defense; Weight = weight; }
    }

    public readonly struct Armour
    {
        public readonly string Name;
        public readonly int Defense;
        public readonly int Weight;
        public Armour(string name, int defense = 0, int weight = 0)
        { Name = name; Defense = defense; Weight = weight; }
    }

    public static class Inventory
    {
        public static readonly Dictionary<Weapons, Weapon> WeaponTable = new Dictionary<Weapons, Weapon>
        {
            { Weapons.NONE,       new Weapon("Punch") },
            { Weapons.GLADIUS,    new Weapon("Gladius", baseDamage: 2, criticalDamage: 8, weight: 1) },
            { Weapons.ZWEIHANDER, new Weapon("Zweihander", baseDamage: 3, criticalDamage: 9, weight: 2) },
        };

        public static readonly Dictionary<Shields, Shield> ShieldTable = new Dictionary<Shields, Shield>
        {
            { Shields.NONE,          new Shield("Bare hand") },
            { Shields.BUCKLER,       new Shield("Buckler", defense: 1, weight: 1) },
            { Shields.WOODEN_SHIELD, new Shield("Wooden Shield", defense: 1, weight: 1) },
            { Shields.IRON_SHIELD,   new Shield("Iron Shield", defense: 2, weight: 2) },
        };

        public static readonly Dictionary<ArmourTypes, Armour> ArmourTable = new Dictionary<ArmourTypes, Armour>
        {
            { ArmourTypes.NONE,          new Armour("Naked") },
            { ArmourTypes.LIGHT_ARMOUR,  new Armour("Light armour", defense: 1, weight: 1) },
            { ArmourTypes.HEAVY_ARMOUR,  new Armour("Heavy armour", defense: 2, weight: 2) },
        };
    }
}