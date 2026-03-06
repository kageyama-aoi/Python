// ─────────────────────────────────────────────
// DERIVE STANDARD PLAN from lectures
// ─────────────────────────────────────────────
function getStandard() {
  if (!config.lectures || config.lectures.length === 0) return null;
  const sorted = [...config.lectures].sort((a,b) => dateToVal(a) - dateToVal(b));
  const firstLec = sorted[0];
  const lastLec  = sorted[sorted.length - 1];
  const baseIn   = addDays(firstLec, -1); // 講義初日の前日
  const baseOut  = lastLec;               // 講義最終日当日
  return { baseIn, baseOut };
}

// ─────────────────────────────────────────────
// PLAN DATE COMPUTATION
// ─────────────────────────────────────────────
function computePlanDates(plan, std) {
  if (plan.daytrip) {
    const startDate = clamp(addDays(std.baseIn, -plan.early), config.timeline.start, config.timeline.end);
    return { startDate, endDate: startDate };
  }
  return {
    startDate: clamp(addDays(std.baseIn,  -plan.early), config.timeline.start, config.timeline.end),
    endDate:   clamp(addDays(std.baseOut,  plan.late),  config.timeline.start, config.timeline.end),
  };
}
