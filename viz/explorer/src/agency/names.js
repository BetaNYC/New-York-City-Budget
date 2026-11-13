/**
 * Agency and unit names in normal case, for the screen only (#307, Noel: "build from this view").
 * The data, links, CSV downloads and old-link matching keep the source capitals; the view shows
 * "Patrol - PS", "Chief of Department - OTPS", "Police Department", with the source name in a
 * title attribute.
 *
 * Acronyms stay in capitals (PS, OTPS, NYC, CUNY, DOE and the like), as do single letters
 * ("Pre-K", "W/C"); "of", "and" and "for" are lowercase except as the first word. "P.S.",
 * "O.T.P.S." and "S.I." become "PS", "OTPS" and "SI", and a dash with a space on either side
 * becomes " - ".
 */
export const ACRONYMS = new Set(
  (
    "PS OTPS OTP NPS OT NYC NY CUNY DOE CCRB OCFS HS GE SI DOC HRA DSS DHS ACS DOT DEP DCAS DOHMH FDNY NYPD EMS IT EEO HIV AIDS " +
    "MTA TLC DFTA SBS HPD DCP DDC DOF DOI DCLA DYCD NYCHA OATH OMB CFB DORIS BIC ECB LPC EDC FISA SCA PSAL TV CEO CW US II III IV"
  ).split(" ")
);
const SMALL = new Set(["of", "and", "for"]);

export function displayName(source) {
  if (source === null || source === undefined) return source;
  const t = String(source)
    .replace(/\bO\.T\.P\.S\./g, "OTPS")
    .replace(/\bP\.\s?S\./g, "PS")
    .replace(/\bS\.I\./g, "SI")
    .replace(/\s+-\s*|\s*-\s+/g, " - ");
  let first = true;
  return t.replace(/[A-Za-z][A-Za-z']*/g, (w) => {
    const isFirst = first;
    first = false;
    const up = w.toUpperCase();
    if (w.length === 1 || ACRONYMS.has(up)) return up;
    const low = w.toLowerCase();
    if (!isFirst && SMALL.has(low)) return low;
    return low[0].toUpperCase() + low.slice(1);
  });
}
