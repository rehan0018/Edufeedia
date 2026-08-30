"""
Curriculum Corpus Test Fixtures.
Used strictly for unit testing, integration tests, and quantitative benchmarks.
Production RAG dynamically queries CurriculumChunk records from PostgreSQL / pgvector.
"""

from typing import List, Dict, Any

CURRICULUM_DOCUMENT_CORPUS: List[Dict[str, Any]] = [
    # Computer Science — Computer Networks & Internet (CBSE Class 10/12)
    {
        "doc_id": "cs_net_intro",
        "subject": "Computer Science",
        "topic": "Computer Networks",
        "grade": 10,
        "section": "Network Fundamentals & Topologies",
        "text": "A computer network is an interconnected group of computing devices (nodes) that communicate and share resources (data, printers, storage) via transmission media (guided cables like fiber optics or unguided wireless radio waves). Common topologies include Star, Bus, Mesh, and Ring."
    },
    {
        "doc_id": "cs_net_types",
        "subject": "Computer Science",
        "topic": "Computer Networks",
        "grade": 10,
        "section": "LAN, MAN, WAN & Network Scales",
        "text": "Networks are categorized by geographic scale: Local Area Network (LAN) spans a room or school campus; Metropolitan Area Network (MAN) spans a city; Wide Area Network (WAN), such as the global Internet, spans across countries and continents using satellite and submarine cable backbones."
    },
    {
        "doc_id": "cs_net_osi_tcp",
        "subject": "Computer Science",
        "topic": "Computer Networks",
        "grade": 10,
        "section": "OSI 7-Layer Model & TCP/IP Protocol Suite",
        "text": "The OSI model standardizes network communication into 7 layers: Physical, Data Link, Network (IP addressing/routing), Transport (TCP reliable byte streams / UDP), Session, Presentation, and Application (HTTP, DNS, SMTP). Packets travel down the sender's stack (encapsulation) and up the receiver's stack (decapsulation)."
    },
    {
        "doc_id": "cs_net_devices_dns",
        "subject": "Computer Science",
        "topic": "Computer Networks",
        "grade": 10,
        "section": "Network Hardware & DNS Resolution",
        "text": "Network hardware includes Routers (which forward packets across different IP subnets), Switches (which switch frames inside a LAN using MAC addresses), and Modems. The Domain Name System (DNS) acts as the phonebook of the internet, translating human-friendly domain names (e.g. edufeedia.org) into numerical IP addresses."
    },
    {
        "doc_id": "cs_net_cybersecurity",
        "subject": "Computer Science",
        "topic": "Computer Networks",
        "grade": 10,
        "section": "Network Security & Encryption",
        "text": "Network security protects transmission confidentiality, integrity, and availability. Firewalls filter unauthorized inbound/outbound packets, while HTTPS/TLS protocols encrypt web payloads using public-key cryptography to prevent packet sniffing and man-in-the-middle attacks."
    },

    # Mathematics — Quadratic Equations (CBSE G10 Chapter 4)
    {
        "doc_id": "math_quad_def",
        "subject": "Mathematics",
        "topic": "Quadratic Equations",
        "grade": 10,
        "section": "Core Definition & Roots Formula",
        "text": "A quadratic equation in variable x is an equation of the form ax² + bx + c = 0, where a, b, c are real numbers and a ≠ 0. The solutions are called roots and given by the quadratic formula x = (-b ± √(b² - 4ac)) / (2a)."
    },
    {
        "doc_id": "math_quad_disc",
        "subject": "Mathematics",
        "topic": "Quadratic Equations",
        "grade": 10,
        "section": "Nature of Roots & Discriminant",
        "text": "The expression D = b² - 4ac is called the discriminant. If D > 0, there are two distinct real roots. If D = 0, there are two equal real roots (x = -b / 2a). If D < 0, there are no real roots (roots are complex conjugate numbers)."
    },
    {
        "doc_id": "math_quad_app",
        "subject": "Mathematics",
        "topic": "Quadratic Equations",
        "grade": 10,
        "section": "Real-World Trajectory Applications",
        "text": "Quadratic functions y = ax² + bx + c graph as symmetrical parabolas. Projectile motion, satellite dish curvatures, and profit-maximization curves are modeled using quadratic vertices."
    },

    # Science — Newton's Laws & Dynamics (CBSE G9/G11 Chapter 9)
    {
        "doc_id": "sci_phys_newton2",
        "subject": "Science",
        "topic": "Newton's Laws",
        "grade": 10,
        "section": "Second Law of Motion (F = ma)",
        "text": "Newton's Second Law states that the rate of change of momentum of a body is directly proportional to the applied unbalanced force: F = dp/dt = m(v - u)/t = ma. Force is measured in Newtons (kg·m/s²)."
    },
    {
        "doc_id": "sci_phys_newton1_3",
        "subject": "Science",
        "topic": "Newton's Laws",
        "grade": 10,
        "section": "First and Third Laws of Motion",
        "text": "Newton's First Law (Law of Inertia) states an object maintains constant velocity unless a net external force acts. The Third Law states that every action has an equal and opposite reaction acting on separate interacting bodies."
    },

    # Science — Electricity & Circuits (CBSE G10 Chapter 12)
    {
        "doc_id": "sci_phys_circuits_ohm",
        "subject": "Science",
        "topic": "Electricity & Circuits",
        "grade": 10,
        "section": "Ohm's Law, Voltage & Current",
        "text": "Ohm's Law states that electric current I flowing through a conductor is directly proportional to the potential difference V across its ends at constant temperature: V = I × R. Resistance R is measured in Ohms (Ω) and depends on conductor length, cross-sectional area, and material resistivity."
    },
    {
        "doc_id": "sci_phys_resistors_comb",
        "subject": "Science",
        "topic": "Electricity & Circuits",
        "grade": 10,
        "section": "Series & Parallel Resistor Networks",
        "text": "In a series circuit, current is identical across all resistors and total resistance is R_total = R₁ + R₂ + R₃. In a parallel circuit, voltage is identical across all branches and equivalent reciprocal resistance is 1/R_total = 1/R₁ + 1/R₂ + 1/R₃."
    },

    # Science — Human Respiration & Bioenergetics (CBSE G10 Chapter 6)
    {
        "doc_id": "sci_resp_aerobic",
        "subject": "Science",
        "topic": "Human Respiration",
        "grade": 10,
        "section": "Aerobic Cellular Respiration & ATP",
        "text": "Aerobic respiration breaks down glucose in the presence of oxygen inside mitochondria to produce carbon dioxide, water, and 36-38 molecules of ATP: C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O + ATP. ATP provides the direct chemical energy for cellular metabolic activities."
    },
    {
        "doc_id": "sci_resp_anaerobic",
        "subject": "Science",
        "topic": "Human Respiration",
        "grade": 10,
        "section": "Anaerobic Respiration & Gas Diffusion",
        "text": "When oxygen supply is insufficient during heavy muscular exertion, pyruvate converts to lactic acid in cytoplasm, causing muscle fatigue. Alveoli in the lungs possess ultra-thin single-cell walls wrapped in extensive capillary networks to maximize gaseous diffusion."
    },

    # Science — Chemical Reactions & Bonding (CBSE G10 Chapter 1/3)
    {
        "doc_id": "sci_chem_reactions",
        "subject": "Science",
        "topic": "Chemical Reactions",
        "grade": 10,
        "section": "Types of Chemical Reactions & Balancing",
        "text": "Chemical reactions involve breaking and making bonds to form new substances. Types include Combination, Decomposition, Single Displacement (more reactive metal displaces less reactive metal), Double Displacement (precipitation), and Redox (Oxidation is loss of electrons; Reduction is gain of electrons)."
    },
    {
        "doc_id": "sci_chem_bonding",
        "subject": "Science",
        "topic": "Chemical Bonding",
        "grade": 10,
        "section": "Ionic & Covalent Bonding Principles",
        "text": "Ionic bonds form by transferring electrons from electropositive metals to electronegative non-metals (e.g. NaCl), creating high melting point crystals. Covalent bonds form by sharing pairs of valence electrons between non-metals to achieve a stable octet (e.g. H₂O, CH₄)."
    },

    # Computer Science — Python Fundamentals & Data Structures
    {
        "doc_id": "cs_py_functions",
        "subject": "Computer Science",
        "topic": "Python Programming",
        "grade": 10,
        "section": "Functions & Modular Scope",
        "text": "In Python, functions defined with 'def' create modular, reusable code blocks. Parameters receive input arguments, local variables have block scope, and the 'return' statement sends values back to the caller."
    },
    {
        "doc_id": "cs_py_loops_data",
        "subject": "Computer Science",
        "topic": "Python Programming",
        "grade": 10,
        "section": "Iteration Loops & Mutable Collections",
        "text": "Python supports 'for' loops iterating over sequences and 'while' loops testing conditional logic. Lists are mutable ordered sequences, whereas dictionaries store key-value mappings with O(1) average lookup times."
    },

    # Mathematics — Trigonometry & Applications (CBSE G10 Chapter 8/9)
    {
        "doc_id": "math_trig_ratios",
        "subject": "Mathematics",
        "topic": "Trigonometry",
        "grade": 10,
        "section": "Trigonometric Ratios in Right Triangles",
        "text": "In a right-angled triangle with acute angle θ: sin(θ) = Opposite/Hypotenuse, cos(θ) = Adjacent/Hypotenuse, tan(θ) = Opposite/Adjacent = sin(θ)/cos(θ). Key fundamental identity: sin²(θ) + cos²(θ) = 1."
    }
]
