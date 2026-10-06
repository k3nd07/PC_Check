"""PCCheck — стоит ли апгрейдить ПК? Оценка по задачам + лучший апгрейд.
Запуск: python pccheck.py   или   python pccheck.py --cpu "i5 12400F" --gpu "RTX 3060" --ram 16 --storage nvme"""
import argparse, difflib, re

# Условные баллы производительности 0..10 (на основе ориентировочных бенчмарков)
CPUS = {"i3 10100":3.5,"i3 12100f":4.8,"i5 8400":3.6,"i5 9400f":3.9,"i5 10400f":4.4,"i5 11400f":5.0,"i5 12400f":6.0,"i5 13400f":6.6,
 "i5 13600k":8.0,"i7 7700":3.9,"i7 9700k":5.8,"i7 12700k":8.2,"i7 13700k":8.8,"i9 13900k":9.6,
 "ryzen 3 3100":3.8,"ryzen 5 2600":3.5,"ryzen 5 3600":4.9,"ryzen 5 5600":6.2,"ryzen 5 5600x":6.4,"ryzen 7 5700x":7.0,"ryzen 7 5800x3d":8.0,
 "ryzen 9 5900x":8.2,"ryzen 5 7600":7.2,"ryzen 7 7700x":8.3,"ryzen 7 7800x3d":9.0,"ryzen 9 7950x":9.7}
GPUS = {"integrated":0.8,"uhd 630":0.8,"vega 8":1.2,"gtx 1050 ti":2.0,"gtx 1650":2.6,"rx 580":2.8,"gtx 1060":3.0,"gtx 1660 super":3.8,"rtx 3050":4.2,
 "rtx 2060":4.6,"rtx 3060":5.5,"rx 6600":5.6,"rx 7600":6.0,"rtx 4060":6.2,"rtx 3060 ti":6.4,"rx 6700 xt":6.9,"rtx 4060 ti":6.9,"rtx 3070":7.0,
 "rtx 4070":7.8,"rx 6800 xt":8.0,"rtx 3080":8.2,"rx 7800 xt":8.2,"rtx 4070 super":8.4,"rtx 4080":9.2,"rx 7900 xtx":9.3,"rtx 4090":10.0}
RAM_SCORE = {4:1.5, 8:3.5, 16:7.0, 32:9.5, 64:10.0}
STORAGE = {"hdd":2.0, "sata":6.5, "nvme":9.0}
# вес компонентов: cpu, gpu, ram, storage
TASKS = {"programming":(0.35,0.05,0.40,0.20), "gaming":(0.30,0.55,0.10,0.05), "video editing":(0.30,0.25,0.30,0.15)}

def norm(s): return re.sub(r"\b(intel|core|amd|nvidia|geforce|radeon|graphics)\b", "", re.sub(r"[-_]", " ", s.lower())).strip()
def lookup(name, table, kind):
    n = " ".join(norm(name).split())
    for key in sorted(table, key=len, reverse=True):          # самое длинное совпадение первым
        if key in n: return key, table[key]
    m = difflib.get_close_matches(n, table, n=1, cutoff=0.55)
    if m: return m[0], table[m[0]]
    raise SystemExit(f"Не знаю {kind} '{name}'. Известные: {', '.join(sorted(table))}")
def ram_score(gb):
    tier = max([k for k in RAM_SCORE if k <= gb] or [4]); return RAM_SCORE[tier]

def rate(cpu, gpu, ram, sto):
    parts = (cpu, gpu, ram_score(ram), STORAGE[sto])
    return {t: round(sum(w*p for w, p in zip(ws, parts)), 1) for t, ws in TASKS.items()}

def upgrades(cpu, gpu, ram, sto):
    opts = []   # (название, новая конфигурация, цена $)
    for g, c in [(16,40),(32,75),(64,150)]:
        if g > ram: opts.append((f"Увеличить RAM до {g} ГБ", (cpu,gpu,g,sto), c))
    for k, c, n in [("nvme",70,"NVMe SSD 1 ТБ"),("sata",45,"SATA SSD 500 ГБ")]:
        if STORAGE[k] > STORAGE[sto]: opts.append((f"Поставить {n}", (cpu,gpu,ram,k), c))
    for n, s, c in [("Ryzen 5 5600 (AM4)",6.2,130),("Ryzen 7 5800X3D (AM4)",8.0,300),("Ryzen 5 7600 (+плата и DDR5)",7.2,450)]:
        if s > cpu + 0.5: opts.append((f"Сменить процессор: {n}", (s,gpu,ram,sto), c))
    for n, s, c in [("RTX 3060",5.5,280),("RX 6700 XT",6.9,320),("RTX 4070",7.8,550),("RTX 4070 Super",8.4,600)]:
        if s > gpu + 0.7: opts.append((f"Сменить видеокарту: {n}", (cpu,s,ram,sto), c))
    return opts

def analyze(cpu_name, gpu_name, ram, sto, focus=None):
    ck, cs = lookup(cpu_name, CPUS, "процессор"); gk, gs = lookup(gpu_name, GPUS, "видеокарту")
    base = rate(cs, gs, ram, sto)
    print(f"\nПроцессор: {ck}  | Видеокарта: {gk}  | RAM: {ram} ГБ  | Накопитель: {sto}\n")
    for t, v in base.items(): print(f"  {t:<14} {v}/10  {'█'*round(v)}{'░'*(10-round(v))}")
    tasks = [focus] if focus in TASKS else list(TASKS)
    ranked = []
    for name, cfg, cost in upgrades(cs, gs, ram, sto):
        new = rate(*cfg); gain = sum(new[t]-base[t] for t in tasks)/len(tasks)
        ranked.append((gain/cost*100, gain, cost, name, new))
    ranked.sort(reverse=True)
    if not ranked: print("\nВаш ПК уже на высоком уровне — апгрейд не нужен."); return
    best = ranked[0]
    print(f"\nBest upgrade: {best[3]}  (~${best[2]}, средний прирост +{best[1]:.1f} балла)")
    print("  после апгрейда: " + ", ".join(f"{t} {v}" for t, v in best[4].items()))
    print("\nДругие варианты:")
    for r in ranked[1:4]: print(f"  • {r[3]} (~${r[2]}): +{r[1]:.1f} балла")
    top = max(r[1] for r in ranked)
    print("\nВердикт:", "апгрейд оправдан" if top >= 1.0 else "прирост небольшой — можно подождать" if top >= 0.4 else "апгрейд почти не даст эффекта")

def main():
    p = argparse.ArgumentParser(); p.add_argument("--cpu"); p.add_argument("--gpu"); p.add_argument("--ram", type=int)
    p.add_argument("--storage", choices=STORAGE); p.add_argument("--focus", choices=TASKS)
    a = p.parse_args()
    cpu = a.cpu or input("Процессор (напр. i5 10400F): "); gpu = a.gpu or input("Видеокарта (напр. GTX 1660 Super): ")
    ram = a.ram or int(input("ОЗУ, ГБ: ")); sto = a.storage or input("Накопитель (hdd / sata / nvme): ").strip().lower()
    if sto not in STORAGE: raise SystemExit("Накопитель: hdd, sata или nvme")
    analyze(cpu, gpu, ram, sto, a.focus)

if __name__ == "__main__": main()
