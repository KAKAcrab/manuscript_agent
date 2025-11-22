-- Pandoc Lua filter: keep only specified top-level sections and stop after certain headers

local keep = {}
local stopset = {}
local active = true
local current_keep = false

local function norm(s)
  s = string.lower(s or ""):gsub("%s+", "")
  local map = {
    ["background"] = "introduction",
    ["materialsandmethods"] = "methods",
    ["patientsandmethods"]  = "methods",
    ["conclusions"]         = "conclusion",
  }
  return map[s] or s
end

function Meta(m)
  if m.keep_sections then
    local ks = pandoc.utils.stringify(m.keep_sections)
    for sec in string.gmatch(ks, '([^,]+)') do
      keep[norm(sec)] = true
    end
  end
  if m.stop_after then
    local sa = pandoc.utils.stringify(m.stop_after)
    for sec in string.gmatch(sa, '([^,]+)') do
      stopset[norm(sec)] = true
    end
  end
  return m
end

function Header(h)
  if not active then
    return {}
  end
  local title = norm(pandoc.utils.stringify(h.content))
  if stopset[title] then
    active = false
    return {}
  end
  current_keep = keep[title] or false
  if not current_keep then
    return {}
  end
end

function Block(el)
  if not active then
    return {}
  end
  if current_keep then
    return el
  else
    return {}
  end
end

