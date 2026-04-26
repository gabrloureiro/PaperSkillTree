from fpdf import FPDF

class DummyPaper(FPDF):
    def header(self):
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, "A Brief Introduction to Neural Networks", 0, 1, "C")
        self.ln(10)

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, 0, 1, "L")
        self.ln(4)

    def chapter_body(self, text):
        self.set_font("Arial", "", 12)
        self.multi_cell(0, 8, text)
        self.ln(10)

pdf = DummyPaper()
pdf.add_page()

pdf.chapter_title("1. Abstract")
pdf.chapter_body(
    "This paper presents a simplified overview of Artificial Neural Networks (ANNs), "
    "their core components, and how they learn. We explore the concepts of Perceptrons, "
    "Activation Functions, Backpropagation, and Gradient Descent."
)

pdf.chapter_title("2. Introduction to Perceptrons")
pdf.chapter_body(
    "A Perceptron is the fundamental building block of a neural network. "
    "It takes multiple binary inputs, applies weights to them, and passes the sum "
    "through a step function to produce an output. It serves as a linear binary classifier."
)

pdf.chapter_title("3. Activation Functions")
pdf.chapter_body(
    "Activation functions introduce non-linear properties to the network. "
    "Without them, no matter how many layers a network has, it would still behave "
    "like a single-layer perceptron because summing linear functions yields a linear function. "
    "Common activation functions include Sigmoid, ReLU, and Tanh."
)

pdf.chapter_title("4. Backpropagation")
pdf.chapter_body(
    "Backpropagation is the primary algorithm used for training neural networks. "
    "It calculates the gradient of the loss function with respect to the weights of the network. "
    "This process involves a forward pass to compute the error, followed by a backward pass "
    "to compute gradients using the chain rule."
)

pdf.chapter_title("5. Gradient Descent")
pdf.chapter_body(
    "Gradient Descent is an optimization algorithm used to minimize the loss function. "
    "By iteratively moving in the direction of steepest descent (the negative of the gradient), "
    "the algorithm updates the network's weights. Learning rate determines the size of the steps "
    "taken towards the minimum."
)

pdf.output("dummy_test.pdf")
print("Generated dummy_test.pdf successfully.")
