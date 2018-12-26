# Grbl requests and responses

## Connection

    <blank line>
    Grbl 1.1f ['$' for help]
    [MSG:'$H'|'$X' to unlock]


## Commands

    g0 x10 y10^Merror:9
    
    $H^Mok
        
    g10 l20 x0 y0 z0^Mok
    
    g0 x10 y10^Mok
    
    ^[[A^Merror:1
    
    g1 x20 y20^Merror:22
    
    g1 x20 y20 f5000^Mok
    
    g1 x30 y30^Mok



