import math

def get_tool_engagement_angle(woc, diameter):
    # SANDVIK - http://www.sandvik.coromant.com/en-us/knowledge/milling/formulas_and_definitions/formulas/pages/default.aspx
    return math.degrees(math.acos(1-((2*min(woc, diameter))/diameter)))

def get_lead_angle_deflection_factor(doc, woc, diameter, helix_angle=30): 
    """
    Returns a tuple of factors (radial, axial) to apply for lead angle
    deflection compensation.
    """
    # Equations from:
    # INGERSOLL Cutting Tools - LEAD angle adjustment to deflection force
    # http://www.ingersoll-imc.com/en/products/ingersoll_cat-009_technical.pdf
    # "As depth of cut decreases, a greater proportion of the cutting force is exerted in the axial direction."
    # http://www.mmsonline.com/articles/the-high-feed-high-reliability-process
    # -- Basically, the force is acting on the rake of the axial cutting edges rather than the radial cutting edges.
    # -- Works for lead-angle and corner-round endmills at low DOC
    #
    # Equation designed by Bryan Turner
    #    X component of the unit normal of DOC/WOC slope, limited to WOC <= RADIUS
    #    Scaled by radial engagement (light radial loads for HSM)
    #    Scaled by the helix angle (higher axial loads for high helix cutters)

    # Not quite correct .. radial/axial forces will not generally add up to 100%
    # of spindle power, rather they have oblique force-multipliers due to lever/fulcrum effects.
    # For now just make them balance.
    if woc < 0 or doc < 0:
        return 1, 1
    radialFactor = min(1,
                       math.cos(math.atan(min(woc, diameter/2) / doc)) *  # Angle of cutter engagement (deep thin slot = 1.0)
                       math.sqrt(woc/diameter) *                          # Scale by radial engagement
                       math.cos(math.radians(helix_angle)))               # Scale by Helix angle

    return radialFactor, 1-radialFactor

def cantilever_deflect_endload(force, length, elasticity, inertia):
    """
    force: N
    length: mm
    elasticity: N/m²
    inertia: mm⁴

    returns deflection in mm
    """
    return force * math.pow(length, 3) / (3*elasticity*inertia)

def cantilever_deflect_uniload(force, length, elasticity, inertia):
    """
    force: N
    length: mm
    elasticity: N/m²
    inertia: mm⁴

    returns deflection in mm
    """
    return (force/length) * math.pow(length, 4) / (8*elasticity*inertia)
