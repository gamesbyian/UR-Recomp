# Course Format Investigation

Goal: produce a ROM-free technical description of Uniracers/Unirally course data and a parser that operates locally on a user-supplied ROM.

## Historical leads

Prior community reverse-engineering reportedly identified Rob Northen Compression for level/course data and successfully decompressed blocks. Treat those reports as leads until reproduced.

## Questions

1. Where is the course index/table?
2. Which RNC method/version is used?
3. What constitutes a course record?
4. What are the dimensions and coordinate units?
5. How are track geometry and visuals related?
6. How are start, finish, checkpoints, hazards, boosts, jumps and stunt-relevant surfaces encoded?
7. Are palettes/themes separate from geometry?
8. Does each course contain metadata or use parallel tables?
9. Can original data be decompressed and losslessly recompressed?
10. Can custom course data be loaded without changing physics code?
