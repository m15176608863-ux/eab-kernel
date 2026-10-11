def overlap(av,bv,x):
    """A+x versus B; translation is rational, with no rounded A.translated()."""
    x=qpoint(x);boundary=False
    den=lcm(*(v.denominator for v in x))
    xi=tuple(v.numerator*(den//v.denominator) for v in x)
    for n,ln,ld,hn,hd in sat_model(av,bv):
        shift=n[0]*xi[0]+n[1]*xi[1]+n[2]*xi[2]
        low,high=shift*ld-ln*den,shift*hd-hn*den
        if low<=0 or high>=0:return -1
        if low==0 or high==0:boundary=True
    return 0 if boundary else 1
