# Chakra UI

Chakra UI is a simple, modular, and accessible component library that gives you the building blocks you need to build React applications with speed and ease. It's built with TypeScript for better type safety and developer experience.

## Table of Contents
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Core Concepts](#core-concepts)
- [Layout Components](#layout-components)
- [Form Components](#form-components)
- [Data Display](#data-display)
- [Feedback](#feedback)
- [Navigation](#navigation)
- [Overlay](#overlay)
- [Theming](#theming)
- [Dark Mode](#dark-mode)
- [Accessibility](#accessibility)
- [Performance](#performance)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)

## Installation

### Prerequisites
- Node.js 12.x or later
- React 16.8.0 or later

### Using npm
```bash
npm install @chakra-ui/react @emotion/react @emotion/styled framer-motion
```

### Using yarn
```bash
yarn add @chakra-ui/react @emotion/react @emotion/styled framer-motion
```

### Peer Dependencies
Chakra UI requires the following peer dependencies:
- `@emotion/react`
- `@emotion/styled`
- `framer-motion`

## Getting Started

### Basic Setup
Wrap your application with the `ChakraProvider`:

```jsx
import * as React from 'react';
import { ChakraProvider } from '@chakra-ui/react';

function App() {
  return (
    <ChakraProvider>
      <YourApp />
    </ChakraProvider>
  );
}

export default App;
```

### First Component
Here's a simple example of a Chakra UI component:

```jsx
import { Box, Button, Heading, Text } from '@chakra-ui/react';

function Welcome() {
  return (
    <Box p={8} maxW="600px" mx="auto">
      <Heading as="h1" size="2xl" mb={4}>
        Welcome to Chakra UI
      </Heading>
      <Text fontSize="xl" mb={8}>
        Build accessible React apps with speed and ease.
      </Text>
      <Button colorScheme="blue" size="lg">
        Get Started
      </Button>
    </Box>
  );
}

export default Welcome;
```

## Core Concepts

### Style Props
Chakra UI uses a style props pattern that allows you to style components directly via props:

```jsx
<Box
  color="white"
  bg="blue.500"
  p={4} // padding
  m={2} // margin
  borderRadius="md" // border radius medium
  _hover={{ bg: 'blue.600' }} // hover state
>
  This is a styled box
</Box>
```

### The `sx` Prop
For more complex styles, use the `sx` prop:

```jsx
<Box
  sx={{
    '& > div': {
      p: 4,
      bg: 'gray.100',
      '&:hover': {
        bg: 'gray.200',
      },
    },
  }}
>
  <div>Hover me</div>
</Box>
```

### Responsive Styles
Use array syntax for responsive styles:

```jsx
<Text
  fontSize={['sm', 'md', 'lg', 'xl']} // responsive font size
  color={['red.500', 'blue.500', 'green.500', 'purple.500']} // responsive color
>
  Responsive Text
</Text>
```

## Layout Components

### Box
A generic container component:

```jsx
<Box 
  p={4} 
  borderWidth="1px" 
  borderRadius="lg"
  _hover={{ shadow: 'md' }}
>
  Box content
</Box>
```

### Flex
A Box with `display: flex`:

```jsx
<Flex 
  direction={['column', 'row']} 
  align="center" 
  justify="space-between"
  p={4}
  gap={4}
>
  <Box>Item 1</Box>
  <Box>Item 2</Box>
  <Box>Item 3</Box>
</Flex>
```

### Grid
A responsive grid layout:

```jsx
<Grid 
  templateColumns={['1fr', 'repeat(2, 1fr)', 'repeat(3, 1fr)']}
  gap={6}
  p={4}
>
  <Box bg="blue.500" h="100px">1</Box>
  <Box bg="green.500" h="100px">2</Box>
  <Box bg="red.500" h="100px">3</Box>
</Grid>
```

### Stack
Stack items vertically or horizontally:

```jsx
<Stack direction={['column', 'row']} spacing={4}>
  <Box bg="yellow.200" p={4}>
    1
  </Box>
  <Box bg="pink.200" p={4}>
    2
  </Box>
  <Box bg="green.200" p={4}>
    3
  </Box>
</Stack>
```

## Form Components

### Form Control
Wrapper for form controls:

```jsx
<FormControl id="email" isRequired isInvalid={!!errors.email}>
  <FormLabel>Email address</FormLabel>
  <Input type="email" {...register('email')} />
  <FormErrorMessage>{errors.email?.message}</FormErrorMessage>
  <FormHelperText>We'll never share your email.</FormHelperText>
</FormControl>
```

### Form Validation with React Hook Form
```jsx
import { useForm } from 'react-hook-form';
import {
  FormControl,
  FormLabel,
  FormErrorMessage,
  Input,
  Button,
  VStack,
} from '@chakra-ui/react';

function ValidationForm() {
  const {
    handleSubmit,
    register,
    formState: { errors, isSubmitting },
  } = useForm();

  function onSubmit(values) {
    return new Promise((resolve) => {
      setTimeout(() => {
        alert(JSON.stringify(values, null, 2));
        resolve();
      }, 3000);
    });
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <VStack spacing={4} align="flex-start">
        <FormControl isInvalid={!!errors.name} isRequired>
          <FormLabel htmlFor="name">Name</FormLabel>
          <Input
            id="name"
            placeholder="Name"
            {...register('name', {
              required: 'Name is required',
              minLength: { value: 3, message: 'Minimum length should be 3' },
            })}
          />
          <FormErrorMessage>
            {errors.name && errors.name.message}
          </FormErrorMessage>
        </FormControl>

        <FormControl isInvalid={!!errors.email} isRequired>
          <FormLabel htmlFor="email">Email</FormLabel>
          <Input
            id="email"
            type="email"
            placeholder="Email"
            {...register('email', {
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address',
              },
            })}
          />
          <FormErrorMessage>
            {errors.email && errors.email.message}
          </FormErrorMessage>
        </FormControl>

        <Button
          mt={4}
          colorScheme="teal"
          isLoading={isSubmitting}
          type="submit"
        >
          Submit
        </Button>
      </VStack>
    </form>
  );
}

export default ValidationForm;
```

### Select Input
```jsx
<Select placeholder="Select option">
  <option value="option1">Option 1</option>
  <option value="option2">Option 2</option>
  <option value="option3">Option 3</option>
</Select>
```

### Checkbox and Radio
```jsx
<Stack spacing={5} direction="row">
  <Checkbox defaultChecked>Checkbox</Checkbox>
  <Checkbox>Checkbox 2</Checkbox>
</Stack>

<RadioGroup defaultValue="1">
  <Stack direction="row">
    <Radio value="1">First</Radio>
    <Radio value="2">Second</Radio>
    <Radio value="3">Third</Radio>
  </Stack>
</RadioGroup>
```

## Data Display

### Card
```jsx
<Card maxW="sm" variant="outline">
  <CardBody>
    <Image
      src="https://images.unsplash.com/photo-1555041469-a586c61ea9bc"
      alt="Green double couch with wooden legs"
      borderRadius="lg"
    />
    <Stack mt="6" spacing="3">
      <Heading size="md">Living room Sofa</Heading>
      <Text>
        This sofa is perfect for modern tropical spaces, baroque inspired
        spaces, earthy toned spaces and for people who love a chic design with a
        sprinkle of vintage design.
      </Text>
      <Text color="blue.600" fontSize="2xl">
        $450
      </Text>
    </Stack>
  </CardBody>
  <Divider />
  <CardFooter>
    <ButtonGroup spacing="2">
      <Button variant="solid" colorScheme="blue">
        Buy now
      </Button>
      <Button variant="ghost" colorScheme="blue">
        Add to cart
      </Button>
    </ButtonGroup>
  </CardFooter>
</Card>
```

### Table
```jsx
<TableContainer>
  <Table variant="simple">
    <TableCaption>Imperial to metric conversion factors</TableCaption>
    <Thead>
      <Tr>
        <Th>To convert</Th>
        <Th>into</Th>
        <Th isNumeric>multiply by</Th>
      </Tr>
    </Thead>
    <Tbody>
      <Tr>
        <Td>inches</Td>
        <Td>millimetres (mm)</Td>
        <Td isNumeric>25.4</Td>
      </Tr>
      <Tr>
        <Td>feet</Td>
        <Td>centimetres (cm)</Td>
        <Td isNumeric>30.48</Td>
      </Tr>
      <Tr>
        <Td>yards</Td>
        <Td>metres (m)</Td>
        <Td isNumeric>0.91444</Td>
      </Tr>
    </Tbody>
    <Tfoot>
      <Tr>
        <Th>To convert</Th>
        <Th>into</Th>
        <Th isNumeric>multiply by</Th>
      </Tr>
    </Tfoot>
  </Table>
</TableContainer>
```

### List
```jsx
<List spacing={3}>
  <ListItem>
    <ListIcon as={CheckCircleIcon} color="green.500" />
    Lorem ipsum dolor sit amet, consectetur adipisicing elit
  </ListItem>
  <ListItem>
    <ListIcon as={CheckCircleIcon} color="green.500" />
    Assumenda, quia temporibus eveniet a libero incidunt suscipit
  </ListItem>
  <ListItem>
    <ListIcon as={CheckCircleIcon} color="green.500" />
    Quidem, ipsam illum quis sed voluptatum quae eum fugit earum
  </ListItem>
</List>
```

## Feedback

### Alert
```jsx
<Stack spacing={3}>
  <Alert status="error">
    <AlertIcon />
    There was an error processing your request
  </Alert>

  <Alert status="success">
    <AlertIcon />
    Data uploaded to the server. Fire on!
  </Alert>

  <Alert status="warning">
    <AlertIcon />
    Seems your account is about to expire, upgrade now.
  </Alert>

  <Alert status="info">
    <AlertIcon />
    Chakra is going live on August 30th. Get ready!
  </Alert>
</Stack>
```

### Toast
```jsx
function Example() {
  const toast = useToast();
  
  return (
    <Button
      onClick={() =>
        toast({
          title: 'Account created.',
          description: "We've created your account for you.",
          status: 'success',
          duration: 9000,
          isClosable: true,
        })
      }
    >
      Show Toast
    </Button>
  );
}
```

### Progress
```jsx
<Stack spacing={5}>
  <Progress hasStripe value={64} />
  <Progress hasStripe colorScheme="red" value={32} />
  <Progress hasStripe colorScheme="green" value={80} />
  <Progress hasStripe colorScheme="pink" size="sm" value={20} />
</Stack>
```

## Navigation

### Menu
```jsx
<Menu>
  <MenuButton as={Button} rightIcon={<ChevronDownIcon />}>
    Actions
  </MenuButton>
  <MenuList>
    <MenuItem>Download</MenuItem>
    <MenuItem>Create a Copy</MenuItem>
    <MenuItem>Mark as Draft</MenuItem>
    <MenuItem>Delete</MenuItem>
    <MenuItem as="a" href="#">
      Attend a Workshop
    </MenuItem>
  </MenuList>
</Menu>
```

### Tabs
```jsx
<Tabs>
  <TabList>
    <Tab>One</Tab>
    <Tab>Two</Tab>
    <Tab>Three</Tab>
  </TabList>

  <TabPanels>
    <TabPanel>
      <p>one!</p>
    </TabPanel>
    <TabPanel>
      <p>two!</p>
    </TabPanel>
    <TabPanel>
      <p>three!</p>
    </TabPanel>
  </TabPanels>
</Tabs>
```

## Overlay

### Modal
```jsx
function BasicUsage() {
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  return (
    <>
      <Button onClick={onOpen}>Open Modal</Button>

      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Modal Title</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text>Modal body text goes here.</Text>
          </ModalBody>

          <ModalFooter>
            <Button colorScheme="blue" mr={3} onClick={onClose}>
              Close
            </Button>
            <Button variant="ghost">Secondary Action</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
```

### Drawer
```jsx
function DrawerExample() {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const btnRef = React.useRef();

  return (
    <>
      <Button ref={btnRef} colorScheme="teal" onClick={onOpen}>
        Open
      </Button>
      <Drawer
        isOpen={isOpen}
        placement="right"
        onClose={onClose}
        finalFocusRef={btnRef}
      >
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader>Create your account</DrawerHeader>

          <DrawerBody>
            <Input placeholder="Type here..." />
          </DrawerBody>

          <DrawerFooter>
            <Button variant="outline" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button colorScheme="blue">Save</Button>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </>
  );
}
```

## Theming

### Extend the Theme
```javascript
// theme.js
import { extendTheme } from '@chakra-ui/react';

const theme = extendTheme({
  colors: {
    brand: {
      50: '#e6fffa',
      100: '#b2f5ea',
      500: '#319795',
      900: '#234e52',
    },
  },
  fonts: {
    heading: 'Inter, sans-serif',
    body: 'Inter, sans-serif',
  },
  components: {
    Button: {
      variants: {
        solid: (props) => ({
          bg: props.colorMode === 'dark' ? 'brand.500' : 'brand.500',
          _hover: {
            bg: props.colorMode === 'dark' ? 'brand.400' : 'brand.600',
          },
        }),
      },
    },
  },
});

export default theme;
```

### Use the Custom Theme
```jsx
import { ChakraProvider, CSSReset } from '@chakra-ui/react';
import theme from './theme';

function App() {
  return (
    <ChakraProvider theme={theme}>
      <CSSReset />
      <YourApp />
    </ChakraProvider>
  );
}
```

## Dark Mode

### Toggle Dark Mode
```jsx
import { useColorMode, Button } from '@chakra-ui/react';
import { MoonIcon, SunIcon } from '@chakra-ui/icons';

function DarkModeToggle() {
  const { colorMode, toggleColorMode } = useColorMode();
  
  return (
    <Button onClick={toggleColorMode}>
      {colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
    </Button>
  );
}
```

### Color Mode Script
Add this to your `_document.js` or HTML head:

```jsx
import { ColorModeScript } from '@chakra-ui/react';
import theme from './theme';

// Inside your document or layout component
<Head>
  <ColorModeScript initialColorMode={theme.config.initialColorMode} />
</Head>
```

## Accessibility

### Focus Management
Chakra UI handles focus management automatically for modals, dialogs, and other interactive components.

### ARIA Attributes
All components come with proper ARIA attributes out of the box.

### Skip Navigation
Add a skip navigation link:

```jsx
<Box as="nav" aria-label="Main navigation">
  <VisuallyHidden>
    <a href="#main-content">Skip to content</a>
  </VisuallyHidden>
  {/* Navigation links */}
</Box>

<main id="main-content">
  {/* Page content */}
</main>
```

## Performance

### Code Splitting
Use dynamic imports for better performance:

```jsx
import dynamic from 'next/dynamic';

const HeavyComponent = dynamic(() => import('../components/HeavyComponent'));

function Home() {
  return (
    <div>
      <HeavyComponent />
    </div>
  );
}
```

### Memoization
Use `React.memo` for expensive components:

```jsx
const ExpensiveComponent = React.memo(function ExpensiveComponent({ data }) {
  return <div>{/* Render something expensive */}</div>;
});
```

## Best Practices

1. **Use Style Props**
   Prefer style props over the `sx` prop for better performance.

2. **Theme Tokens**
   Use theme tokens for consistent styling:
   ```jsx
   <Box color="gray.600" fontSize="lg">
     Using theme tokens
   </Box>
   ```

3. **Responsive Styles**
   Use array syntax for responsive styles:
   ```jsx
   <Box p={[2, 4, 6]}>
     Responsive padding
   </Box>
   ```

4. **Component Composition**
   Compose smaller components for better reusability.

5. **Accessibility**
   - Use semantic HTML elements
   - Add proper ARIA labels
   - Ensure keyboard navigation works

## Troubleshooting

### Common Issues

1. **Styles Not Applying**
   - Ensure `ChakraProvider` is at the root of your app
   - Check for CSS specificity issues

2. **TypeScript Errors**
   - Make sure to install `@types/react` and `@types/react-dom`
   - Check component prop types

3. **Performance Issues**
   - Use React DevTools to identify re-renders
   - Memoize expensive computations

## Resources

- [Official Documentation](https://chakra-ui.com/)
- [GitHub Repository](https://github.com/chakra-ui/chakra-ui/)
- [Chakra UI Templates](https://chakra-templates.dev/)
- [Chakra UI Figma Kit](https://www.figma.com/community/file/971408767069651099)
- [Awesome Chakra UI](https://github.com/chakra-ui/awesome-chakra-ui)

## License

Chakra UI is licensed under the MIT License. See the [LICENSE](https://github.com/chakra-ui/chakra-ui/blob/main/LICENSE) file for more information.
