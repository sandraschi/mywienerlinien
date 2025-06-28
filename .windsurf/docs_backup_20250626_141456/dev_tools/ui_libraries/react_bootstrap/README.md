# React Bootstrap

React Bootstrap is a complete re-implementation of the Bootstrap components using React. It provides native React components with no dependency on jQuery or Bootstrap's JavaScript, offering better performance and a more idiomatic React experience.

## Table of Contents
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Core Concepts](#core-concepts)
- [Layout](#layout)
- [Forms](#forms)
- [Components](#components)
- [Theming](#theming)
- [Accessibility](#accessibility)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)

## Installation

### Prerequisites
- Node.js 12 or later
- React 16.8 or later
- A React project set up with a package manager (npm or yarn)

### Install React Bootstrap

```bash
# Using npm
npm install react-bootstrap bootstrap

# Using yarn
yarn add react-bootstrap bootstrap
```

### Import CSS

Import Bootstrap CSS in your `src/index.js` or `App.js` file:

```jsx
import 'bootstrap/dist/css/bootstrap.min.css';
```

### Optional: Install Icons

For Bootstrap Icons:

```bash
# Using npm
npm install react-bootstrap-icons

# Using yarn
yarn add react-bootstrap-icons
```

## Getting Started

### Basic Example

```jsx
import React from 'react';
import { Button } from 'react-bootstrap';

function App() {
  return (
    <div className="App">
      <Button variant="primary">Click me</Button>
    </div>
  );
}

export default App;
```

### Using Icons

```jsx
import { House, Gear, Person } from 'react-bootstrap-icons';

function Navigation() {
  return (
    <div>
      <House className="me-2" /> Home
      <Gear className="me-2" /> Settings
      <Person /> Profile
    </div>
  );
}
```

## Core Concepts

### Components

React Bootstrap provides Bootstrap components as React components. Each component is imported individually to keep your bundle size small.

### Styling

- Uses Bootstrap's utility classes
- Supports custom theming via SASS variables
- Responsive design built-in

### Accessibility

- Follows WAI-ARIA standards
- Keyboard navigation support
- Screen reader friendly

## Layout

### Container

```jsx
import { Container } from 'react-bootstrap';

function Layout() {
  return (
    <Container>
      {/* Content goes here */}
    </Container>
  );
}
```

### Grid System

```jsx
import { Container, Row, Col } from 'react-bootstrap';

function GridExample() {
  return (
    <Container>
      <Row>
        <Col sm={8}>sm=8</Col>
        <Col sm={4}>sm=4</Col>
      </Row>
      <Row>
        <Col sm>sm=true</Col>
        <Col sm>sm=true</Col>
        <Col sm>sm=true</Col>
      </Row>
    </Container>
  );
}
```

## Forms

### Basic Form

```jsx
import { Form, Button } from 'react-bootstrap';

function BasicForm() {
  return (
    <Form>
      <Form.Group className="mb-3" controlId="formBasicEmail">
        <Form.Label>Email address</Form.Label>
        <Form.Control type="email" placeholder="Enter email" />
        <Form.Text className="text-muted">
          We'll never share your email with anyone else.
        </Form.Text>
      </Form.Group>

      <Form.Group className="mb-3" controlId="formBasicPassword">
        <Form.Label>Password</Form.Label>
        <Form.Control type="password" placeholder="Password" />
      </Form.Group>

      <Form.Group className="mb-3" controlId="formBasicCheckbox">
        <Form.Check type="checkbox" label="Check me out" />
      </Form.Group>

      <Button variant="primary" type="submit">
        Submit
      </Button>
    </Form>
  );
}
```

### Form Validation

```jsx
import { useState } from 'react';
import { Form, Button, Alert } from 'react-bootstrap';

function FormWithValidation() {
  const [validated, setValidated] = useState(false);
  const [showAlert, setShowAlert] = useState(false);

  const handleSubmit = (event) => {
    const form = event.currentTarget;
    event.preventDefault();
    
    if (form.checkValidity() === false) {
      event.stopPropagation();
    } else {
      setShowAlert(true);
    }
    
    setValidated(true);
  };

  return (
    <>
      {showAlert && (
        <Alert variant="success" onClose={() => setShowAlert(false)} dismissible>
          <Alert.Heading>Form submitted successfully!</Alert.Heading>
          <p>Your information has been saved.</p>
        </Alert>
      )}
      
      <Form noValidate validated={validated} onSubmit={handleSubmit}>
        <Form.Group className="mb-3" controlId="validationCustom01">
          <Form.Label>First name</Form.Label>
          <Form.Control
            required
            type="text"
            placeholder="First name"
            defaultValue=""
          />
          <Form.Control.Feedback>Looks good!</Form.Control.Feedback>
          <Form.Control.Feedback type="invalid">
            Please provide a first name.
          </Form.Control.Feedback>
        </Form.Group>

        <Form.Group className="mb-3" controlId="validationCustom02">
          <Form.Label>Last name</Form.Label>
          <Form.Control
            required
            type="text"
            placeholder="Last name"
            defaultValue=""
          />
          <Form.Control.Feedback>Looks good!</Form.Control.Feedback>
          <Form.Control.Feedback type="invalid">
            Please provide a last name.
          </Form.Control.Feedback>
        </Form.Group>

        <Form.Group className="mb-3" controlId="validationCustomUsername">
          <Form.Label>Username</Form.Label>
          <InputGroup hasValidation>
            <InputGroup.Text id="inputGroupPrepend">@</InputGroup.Text>
            <Form.Control
              type="text"
              placeholder="Username"
              aria-describedby="inputGroupPrepend"
              required
            />
            <Form.Control.Feedback type="invalid">
              Please choose a username.
            </Form.Control.Feedback>
          </InputGroup>
        </Form.Group>

        <Button type="submit">Submit form</Button>
      </Form>
    </>
  );
}
```

## Components

### Navigation

#### Navbar

```jsx
import { Navbar, Nav, Container, NavDropdown } from 'react-bootstrap';

function Navigation() {
  return (
    <Navbar bg="light" expand="lg">
      <Container>
        <Navbar.Brand href="#home">React-Bootstrap</Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link href="#home">Home</Nav.Link>
            <Nav.Link href="#link">Link</Nav.Link>
            <NavDropdown title="Dropdown" id="basic-nav-dropdown">
              <NavDropdown.Item href="#action/3.1">Action</NavDropdown.Item>
              <NavDropdown.Item href="#action/3.2">Another action</NavDropdown.Item>
              <NavDropdown.Item href="#action/3.3">Something</NavDropdown.Item>
              <NavDropdown.Divider />
              <NavDropdown.Item href="#action/3.4">Separated link</NavDropdown.Item>
            </NavDropdown>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}
```

### Cards

```jsx
import { Card, Button } from 'react-bootstrap';

function ProductCard() {
  return (
    <Card style={{ width: '18rem' }}>
      <Card.Img variant="top" src="holder.js/100px180" />
      <Card.Body>
        <Card.Title>Card Title</Card.Title>
        <Card.Text>
          Some quick example text to build on the card title and make up the
          bulk of the card's content.
        </Card.Text>
        <Button variant="primary">Go somewhere</Button>
      </Card.Body>
    </Card>
  );
}
```

### Modals

```jsx
import { useState } from 'react';
import { Button, Modal } from 'react-bootstrap';

function Example() {
  const [show, setShow] = useState(false);

  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);

  return (
    <>
      <Button variant="primary" onClick={handleShow}>
        Launch demo modal
      </Button>

      <Modal show={show} onHide={handleClose}>
        <Modal.Header closeButton>
          <Modal.Title>Modal heading</Modal.Title>
        </Modal.Header>
        <Modal.Body>Woohoo, you're reading this text in a modal!</Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Close
          </Button>
          <Button variant="primary" onClick={handleClose}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}
```

### Tables

```jsx
import { Table } from 'react-bootstrap';

function DataTable() {
  return (
    <Table striped bordered hover>
      <thead>
        <tr>
          <th>#</th>
          <th>First Name</th>
          <th>Last Name</th>
          <th>Username</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>1</td>
          <td>Mark</td>
          <td>Otto</td>
          <td>@mdo</td>
        </tr>
        <tr>
          <td>2</td>
          <td>Jacob</td>
          <td>Thornton</td>
          <td>@fat</td>
        </tr>
        <tr>
          <td>3</td>
          <td colSpan={2}>Larry the Bird</td>
          <td>@twitter</td>
        </tr>
      </tbody>
    </Table>
  );
}
```

## Theming

### Customizing with SASS

1. Create a custom SCSS file (e.g., `custom.scss`):

```scss
// Custom.scss
// Option A: Include all of Bootstrap
@import "~bootstrap/scss/bootstrap";

// Then add additional custom code here

// Custom variables
$primary: #0074d9;
$danger: #ff4136;

// Custom styles
body {
  padding-top: 2rem;
}
```

2. Import the custom SCSS file in your `index.js` or `App.js`:

```jsx
import './custom.scss';
```

### Theming with CSS Variables

```css
:root {
  --bs-primary: #0d6efd;
  --bs-secondary: #6c757d;
  --bs-success: #198754;
  --bs-info: #0dcaf0;
  --bs-warning: #ffc107;
  --bs-danger: #dc3545;
  --bs-light: #f8f9fa;
  --bs-dark: #212529;
}

body {
  --bs-body-font-family: var(--bs-font-sans-serif);
  --bs-body-font-size: 1rem;
  --bs-body-font-weight: 400;
  --bs-body-line-height: 1.5;
  --bs-body-color: #212529;
  --bs-body-bg: #fff;
}
```

## Accessibility

### Keyboard Navigation

All interactive components support keyboard navigation:
- Buttons are focusable and can be activated with Space or Enter
- Dropdowns can be navigated with arrow keys
- Modals trap focus and can be closed with Escape

### ARIA Attributes

React Bootstrap components include appropriate ARIA attributes:

```jsx
<Button 
  variant="primary" 
  aria-label="Close"
  aria-expanded={isOpen}
  aria-controls="example-collapse-text"
>
  Toggle
</Button>
```

### Skip Links

Add skip links for keyboard users:

```jsx
import { Container, Nav } from 'react-bootstrap';

function SkipLink() {
  return (
    <Container>
      <a href="#main-content" className="visually-hidden-focusable">
        Skip to main content
      </a>
      
      <Nav>
        {/* Navigation items */}
      </Nav>
      
      <main id="main-content">
        {/* Main content */}
      </main>
    </Container>
  );
}
```

## Best Practices

### Component Imports

Import only the components you need to keep bundle size small:

```jsx
// Good: Import only what you need
import { Button } from 'react-bootstrap';

// Bad: Avoid importing everything
import { Button } from 'react-bootstrap';
```

### Custom Components

Create reusable components that encapsulate common patterns:

```jsx
// components/AlertMessage.jsx
import { Alert } from 'react-bootstrap';

function AlertMessage({ variant = 'info', children }) {
  return (
    <Alert variant={variant} className="mb-4">
      {children}
    </Alert>
  );
}

export default AlertMessage;
```

### Performance Optimization

1. **Code Splitting**
   Use React.lazy and Suspense for code splitting:

   ```jsx
   import { lazy, Suspense } from 'react';
   import { Spinner } from 'react-bootstrap';
   
   const HeavyComponent = lazy(() => import('./HeavyComponent'));
   
   function App() {
     return (
       <Suspense fallback={
         <div className="text-center p-5">
           <Spinner animation="border" role="status">
             <span className="visually-hidden">Loading...</span>
           </Spinner>
         </div>
       }>
         <HeavyComponent />
       </Suspense>
     );
   }
   ```

2. **Memoization**
   Use React.memo for expensive components:

   ```jsx
   import { memo } from 'react';
   import { Card } from 'react-bootstrap';
   
   const ExpensiveCard = memo(function ExpensiveCard({ data }) {
     // Expensive rendering logic
     return (
       <Card>
         {/* Card content */}
       </Card>
     );
   });
   ```

## Troubleshooting

### Common Issues

1. **Styles Not Applying**
   - Ensure `bootstrap/dist/css/bootstrap.min.css` is imported
   - Check for CSS specificity issues
   - Verify your custom styles are loaded after Bootstrap

2. **JavaScript Errors**
   - Make sure you're using compatible versions of React and React DOM
   - Check the browser console for specific error messages
   - Ensure all required dependencies are installed

3. **Component Not Rendering**
   - Check for typos in component names (they're case-sensitive)
   - Verify the component is properly imported
   - Make sure the component is used within a valid parent component

## Resources

- [Official Documentation](https://react-bootstrap.github.io/)
- [GitHub Repository](https://github.com/react-bootstrap/react-bootstrap)
- [Bootstrap Documentation](https://getbootstrap.com/)
- [React Bootstrap Icons](https://github.com/ismamz/react-bootstrap-icons)
- [CodeSandbox Examples](https://react-bootstrap.github.io/getting-started/examples/)

## License

React Bootstrap is MIT licensed. See the [LICENSE](https://github.com/react-bootstrap/react-bootstrap/blob/master/LICENSE) file for more details.
