// QR Code Payment Handling for VREC Library Management System

// QRPayment Class
class QRPayment {
    constructor(containerId) {
        this.containerId = containerId;
    }

    generateQR(data) {
        const container = document.getElementById(this.containerId);
        container.innerHTML = '';
        
        return QRCode.toCanvas(container, data, {
            width: 256,
            margin: 1,
            color: {
                dark: '#000000',
                light: '#ffffff'
            }
        });
    }

    generateUPILink(paymentData) {
        const {
            payeeName = 'VREC Library',
            payeeVPA = 'library@upi',
            amount,
            transactionNote
        } = paymentData;

        return `upi://pay?pa=${payeeVPA}&pn=${encodeURIComponent(payeeName)}&am=${amount}&cu=INR&tn=${encodeURIComponent(transactionNote)}`;
    }
}

// Initialize QRPayment instance
const qrPayment = new QRPayment('qrCode');

// Function to show QR payment modal
function showQRPayment(bookId) {
    const modal = document.getElementById('qrPaymentModal');
    modal.classList.remove('hidden');
    
    // Generate QR code for payment
    const upiLink = qrPayment.generateUPILink({
        amount: 10.00,
        transactionNote: `Book Preorder ${bookId}`
    });
    
    qrPayment.generateQR(upiLink);
}

// Function to close QR modal
function closeQRModal() {
    document.getElementById('qrPaymentModal').classList.add('hidden');
}

// Function to confirm payment
async function confirmPayment() {
    try {
        // Simulate payment verification
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        showToast('Payment successful! Book has been preordered.', 'success');
        closeQRModal();
        loadDashboardData(); // Refresh dashboard data
        
    } catch (error) {
        console.error('Error confirming payment:', error);
        showToast('Failed to confirm payment', 'error');
    }
}