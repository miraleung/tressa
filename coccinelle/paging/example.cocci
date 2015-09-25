@pktset@
typedef Packet;
identifier p;
identifier func;
position p0;
@@

func(...) {
...
Packet *p@p0 = SCMalloc(...);
...
}

@pktdata@
identifier pktset.p;
identifier pktset.func;
position p1;
@@

func(...) {
...
Packet *p = SCMalloc(...);
...
(
p@p1->pkt = ...
)
...
}

@pktzero@
identifier pktset.p;
identifier pktset.func;
position p2;
@@

func(...) {
...
Packet *p = SCMalloc(...);
...
(
memset(p@p2, 0, ...)
)
...
}

@script:python depends on !pktdata@
p0 << pktset.p0;
@@

print "%s: No pkt setting for Packet* allocated at %s" % (p0[0].file, p0[0].line)

@script:python depends on pktset && pktdata && pktzero@
p0 << pktset.p0;
p1 << pktdata.p1;
p2 << pktzero.p2;
@@

if int(p1[0].line) <= int(p2[0].line):
	print "%s: Packet data set at %s but zeroed at %s" % (p1[0].file, p1[0].line, p2[0].line)
